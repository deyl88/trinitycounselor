"""
AES-256-GCM symmetric encryption for per-user content.

Primitives:
  encrypt_text(plaintext, key) -> bytes   (nonce || ciphertext || tag)
  decrypt_text(ciphertext, key) -> str

The 12-byte random nonce is prepended to the ciphertext on every call,
so encrypting the same plaintext twice produces different outputs (IND-CPA).
"""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_text(plaintext: str, key: bytes) -> bytes:
    """
    Encrypt a UTF-8 string with AES-256-GCM.

    Returns: nonce (12 bytes) || ciphertext+tag bytes
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits).")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_text(data: bytes, key: bytes) -> str:
    """
    Decrypt AES-256-GCM blob produced by encrypt_text.

    Returns the original UTF-8 plaintext.
    Raises cryptography.exceptions.InvalidTag on tampered data.
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits).")
    if len(data) < 12:
        raise ValueError("Ciphertext too short — missing nonce.")
    aesgcm = AESGCM(key)
    nonce, ciphertext = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
