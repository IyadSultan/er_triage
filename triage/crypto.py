"""PHI-protection helpers: MRN obfuscation + patient-name encryption.

This mirrors the KHCC convention the course teaches:
  * MRNs are *Optimus-encoded* before storage — a reversible integer transform
    so the raw MRN never sits in the database as-is, but can still be decoded
    when needed.
  * Patient names are *Fernet-encrypted* at rest, and never logged.

Both use dev-safe fallbacks so the app runs out of the box. In production,
set OPTIMUS_RANDOM and FERNET_KEY as environment variables (Render dashboard).

NOTE: this is teaching-grade PHI handling. A real clinical deployment uses the
AI Office's managed key vault, not env vars with dev fallbacks.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

# --- Optimus: reversible MRN obfuscation ------------------------------------
# Operates in the ring of integers mod 2**31. PRIME must be odd (coprime to the
# modulus); the modular inverse is computed at import so the pair is always
# valid — no magic-constant bugs.
_MOD = 1 << 31
_MASK = _MOD - 1
_PRIME = 1_580_030_173  # odd
_RANDOM = int(os.environ.get("OPTIMUS_RANDOM", "1163945558")) & _MASK
_INVERSE = pow(_PRIME, -1, _MOD)


def encode_mrn(mrn: str | int) -> str:
    """Encode a numeric MRN to its Optimus form (returned as a string)."""
    n = int(mrn)
    encoded = ((n * _PRIME) & _MASK) ^ _RANDOM
    return str(encoded)


def decode_mrn(encoded: str | int) -> str:
    """Reverse :func:`encode_mrn`."""
    x = int(encoded)
    n = ((x ^ _RANDOM) * _INVERSE) & _MASK
    return str(n)


# --- Fernet: patient-name encryption ----------------------------------------
def _fernet() -> Fernet:
    key = os.environ.get("FERNET_KEY")
    if not key:
        # Deterministic dev key so the same DB stays readable across restarts.
        key = base64.urlsafe_b64encode(
            hashlib.sha256(b"cci-session-11-dev-fernet").digest()
        ).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_name(name: str) -> bytes:
    """Encrypt a patient name. Returns ciphertext bytes for a BinaryField."""
    return _fernet().encrypt(name.encode("utf-8"))


def decrypt_name(token: bytes) -> str:
    """Decrypt a name. Returns '<unreadable>' if the key has changed."""
    if not token:
        return ""
    try:
        return _fernet().decrypt(bytes(token)).decode("utf-8")
    except InvalidToken:
        return "<unreadable: key mismatch>"
