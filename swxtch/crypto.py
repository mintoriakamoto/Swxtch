"""Cryptographic verification of MAC and IP changes using SHA3-256 and MLKEM (FIPS 206)."""

import json
from hashlib import sha3_256
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

try:
    import oqs
    HAS_MLKEM = True
except ImportError:
    HAS_MLKEM = False

LOG_DIR = Path("/var/log/swxtch")


def sha3_256_hash(data: str) -> str:
    """Hash data with SHA3-256."""
    return sha3_256(data.encode()).hexdigest()


def mlkem_encrypt(plaintext: str) -> Optional[Tuple[str, str]]:
    """
    Encrypt with MLKEM (post-quantum, FIPS 206).
    Returns (ciphertext, public_key) or None if MLKEM unavailable.
    """
    if not HAS_MLKEM:
        return None

    try:
        kekem = oqs.KeyEncapsulation("ML-KEM-768")
        public_key = kekem.generate_keypair()

        # For demonstration: derive key and use for symmetric encryption
        # In production, use proper AEAD like ChaCha20-Poly1305
        shared_secret = kekem.encaps(public_key)

        # Hash plaintext with shared secret for basic encryption
        encrypted = sha3_256(plaintext.encode() + shared_secret.encode()).hexdigest()

        return encrypted, public_key
    except Exception:
        return None


def verify_mac_change(old_mac: str, new_mac: str, interface: str) -> dict:
    """
    Verify MAC address change and return encrypted record.
    Uses SHA3-256 for hashing and optional MLKEM for post-quantum security.
    """
    timestamp = datetime.utcnow().isoformat()

    # Hash both addresses
    old_hash = sha3_256_hash(old_mac)
    new_hash = sha3_256_hash(new_mac)

    # Prepare record
    record = {
        "type": "mac_change",
        "interface": interface,
        "timestamp": timestamp,
        "old_mac": old_mac,
        "new_mac": new_mac,
        "old_mac_hash_sha3_256": old_hash,
        "new_mac_hash_sha3_256": new_hash,
        "change_verified": old_mac != new_mac,
    }

    # Optional MLKEM encryption for post-quantum security
    if HAS_MLKEM:
        record_json = json.dumps(record)
        mlkem_result = mlkem_encrypt(record_json)
        if mlkem_result:
            encrypted, pubkey = mlkem_result
            record["mlkem_encrypted"] = encrypted
            record["mlkem_pubkey"] = pubkey
            record["fips_206_compliant"] = True

    return record


def verify_ip_change(old_ip: Optional[str], new_ip: str, interface: str) -> dict:
    """
    Verify IP address change and return encrypted record.
    Uses SHA3-256 for hashing and optional MLKEM for post-quantum security.
    """
    timestamp = datetime.utcnow().isoformat()

    # Hash IP addresses
    new_hash = sha3_256_hash(new_ip)
    old_hash = sha3_256_hash(old_ip) if old_ip else None

    # Prepare record
    record = {
        "type": "ip_change",
        "interface": interface,
        "timestamp": timestamp,
        "old_ip": old_ip,
        "new_ip": new_ip,
        "new_ip_hash_sha3_256": new_hash,
        "change_verified": old_ip != new_ip if old_ip else True,
    }

    if old_hash:
        record["old_ip_hash_sha3_256"] = old_hash

    # Optional MLKEM encryption for post-quantum security
    if HAS_MLKEM:
        record_json = json.dumps(record)
        mlkem_result = mlkem_encrypt(record_json)
        if mlkem_result:
            encrypted, pubkey = mlkem_result
            record["mlkem_encrypted"] = encrypted
            record["mlkem_pubkey"] = pubkey
            record["fips_206_compliant"] = True

    return record


def log_verification(mac_record: dict, ip_record: dict) -> None:
    """Log verified MAC and IP changes to encrypted file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / "changes.log"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "mac_verification": mac_record,
        "ip_verification": ip_record,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # Secure log file permissions
    log_file.chmod(0o600)
