"""
Per-user encryption key management.

Each user gets a unique 256-bit AES key at registration.
That key is encrypted with the system MASTER_KEY (AES-256-GCM) and stored
in the database. This is a simplified KMS pattern — in production consider
AWS KMS or HashiCorp Vault for envelope key management.

Flow:
  1. At registration: generate user_key → encrypt with master_key → store
  2. At runtime:      load encrypted_key from DB → decrypt with master_key → use
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.config import settings


def _master_key_bytes() -> bytes:
    raw = base64.urlsafe_b64decode(settings.master_key + "==")
    if len(raw) != 32:
        raise ValueError("MASTER_KEY must decode to exactly 32 bytes (256 bits).")
    return raw


def generate_user_key() -> bytes:
    """Generate a fresh 256-bit user encryption key."""
    return os.urandom(32)


def encrypt_user_key(user_key: bytes) -> str:
    """
    Encrypt a user's key with the system master key.
    Returns base64-encoded: nonce (12 bytes) || ciphertext (32 bytes) || tag (16 bytes).
    """
    master = _master_key_bytes()
    aesgcm = AESGCM(master)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, user_key, None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_user_key(encrypted_key: str) -> bytes:
    """Decrypt and return the raw 32-byte user key."""
    master = _master_key_bytes()
    aesgcm = AESGCM(master)
    data = base64.urlsafe_b64decode(encrypted_key + "==")
    nonce, ciphertext = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
