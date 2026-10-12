"""Password hashing helpers for BakeSync (PBKDF2-HMAC-SHA256, per-user salt)."""
import hashlib
import hmac
import os

_ALGO = "pbkdf2"
_ITERATIONS = 200_000


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(_ALGO + "$")


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(stored, supplied):
    """True if `supplied` matches `stored`. A value that was never hashed
    (legacy plaintext row) is compared directly so it can still be upgraded."""
    if not stored or supplied is None:
        return False
    if not is_hashed(stored):
        return hmac.compare_digest(stored.encode("utf-8"), supplied.encode("utf-8"))
    try:
        _, iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", supplied.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"


def password_strength_error(password):
    """Same rules as the sign-up form. Returns a message, or None if the password is OK."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not (any(c.isupper() for c in password) and any(c.islower() for c in password)):
        return "Password needs both uppercase and lowercase letters."
    if not any(c.isdigit() for c in password):
        return "Password needs at least one number."
    if not any(c in SPECIAL_CHARS for c in password):
        return "Password needs at least one special character (e.g. ! @ # $)."
    return None
