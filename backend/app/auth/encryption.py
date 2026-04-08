"""Per-user data encryption for private memory stores.

Privacy Model
─────────────
Each partner's private conversation memory is encrypted at rest with a
key derived from their credentials. This is Layer 1 of the privacy model:
even a DB admin cannot read Partner A's private disclosures.

Key Derivation
──────────────
We use PBKDF2-HMAC-SHA256 to derive a 256-bit Data Encryption Key (DEK)
from (user_id + password + app-level salt). The DEK is never stored —
it is re-derived at request time from the user's password.

For production, consider envelope encryption: derive a DEK per user,
encrypt the DEK with the MASTER_ENCRYPTION_KEY, store the encrypted DEK
in the users table. This avoids re-deriving on every request.

Status: STUB — interfaces fully defined, crypto operations wired.
The integration point (wrapping encrypt/decrypt around pgvector content)
is marked TODO in pgvector_store.py.
"""

import hashlib
import os
from base64 import b64decode, b64encode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

# Salt for PBKDF2 key derivation — NOT a secret, just domain separation.
# The actual security comes from the user's password.
_KDF_SALT_PREFIX = b"trinity_v1_user_key:"

_PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation for SHA-256


def derive_user_key(user_id: str, password: str) -> bytes:
    """Derive a 256-bit AES key from a user's credentials.

    Args:
        user_id: UUID string of the user (domain-separates keys across users).
        password: The user's plaintext password (never stored).

    Returns:
        32-byte key suitable for AES-256-GCM.

    Notes:
        - This is deterministic: same inputs → same key, always.
        - Key is never persisted. Re-derive per authenticated request.
        - For high-throughput systems, cache the derived key in an
          encrypted, short-TTL Redis entry keyed by session token.
    """
    salt = _KDF_SALT_PREFIX + user_id.encode()
    key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode(),
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
        dklen=32,
    )
    return key


def encrypt_bytes(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt bytes with AES-256-GCM.

    Args:
        plaintext: Raw bytes to encrypt.
        key: 32-byte AES key (from `derive_user_key`).

    Returns:
        Nonce (12 bytes) + ciphertext + GCM tag, base64-encoded.
        The nonce is randomly generated per call and prepended to the
        ciphertext so decrypt_bytes can extract it.
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return b64encode(nonce + ciphertext)


def decrypt_bytes(encrypted: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM ciphertext produced by `encrypt_bytes`.

    Args:
        encrypted: Base64-encoded nonce + ciphertext from `encrypt_bytes`.
        key: 32-byte AES key (from `derive_user_key`).

    Returns:
        Original plaintext bytes.

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data).
    """
    raw = b64decode(encrypted)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    except Exception as exc:
        raise ValueError("Decryption failed — wrong key or corrupted ciphertext.") from exc


def get_master_key() -> bytes:
    """Return the application-level master encryption key.

    Used for envelope encryption of per-user DEKs (future enhancement).
    Currently validates that MASTER_ENCRYPTION_KEY is a valid 32-byte hex string.
    """
    settings = get_settings()
    raw = settings.master_encryption_key
    try:
        key = bytes.fromhex(raw)
    except ValueError as exc:
        raise ValueError(
            "MASTER_ENCRYPTION_KEY must be a 64-character hex string (32 bytes). "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        ) from exc
    if len(key) != 32:
        raise ValueError("MASTER_ENCRYPTION_KEY must be exactly 32 bytes (64 hex chars).")
    return key
