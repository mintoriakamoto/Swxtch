"""Tests for advanced post-quantum cryptography module."""

import json
import secrets
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import pytest

from swxtch.crypto import (
    PostQuantumCrypto,
    get_crypto,
    EncryptedData,
    verify_mac_change,
    verify_ip_change,
    log_verification,
)


class TestPostQuantumCrypto:
    """Test post-quantum cryptography implementation."""

    def test_initialization(self):
        """Should initialize crypto system."""
        crypto = PostQuantumCrypto()
        assert crypto.master_key is not None
        assert len(crypto.master_key) == 32

    def test_master_key_persistence(self):
        """Master key should persist across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("swxtch.crypto.MASTER_KEY_FILE", Path(tmpdir) / "master.key"):
                crypto1 = PostQuantumCrypto()
                key1 = crypto1.master_key

                crypto2 = PostQuantumCrypto()
                key2 = crypto2.master_key

                assert key1 == key2

    def test_derive_key(self):
        """Should derive key from password."""
        crypto = PostQuantumCrypto()
        key, salt = crypto._derive_key("test_password")

        assert len(key) == 32
        assert len(salt) == 16
        assert isinstance(key, bytes)
        assert isinstance(salt, bytes)

    def test_derive_key_deterministic(self):
        """Same password + salt should produce same key."""
        crypto = PostQuantumCrypto()
        salt = secrets.token_bytes(16)

        key1, _ = crypto._derive_key("password", salt)
        key2, _ = crypto._derive_key("password", salt)

        assert key1 == key2

    def test_derive_key_different_password(self):
        """Different passwords should produce different keys."""
        crypto = PostQuantumCrypto()
        salt = secrets.token_bytes(16)

        key1, _ = crypto._derive_key("password1", salt)
        key2, _ = crypto._derive_key("password2", salt)

        assert key1 != key2


class TestSessionKeyManagement:
    """Test session key management with PFS."""

    def test_session_key_generation(self):
        """Should generate session key."""
        crypto = PostQuantumCrypto()
        key = crypto.get_session_key()

        assert len(key) == 32
        assert isinstance(key, bytes)

    def test_session_key_persistent(self):
        """Session key should persist within lifetime."""
        crypto = PostQuantumCrypto()
        key1 = crypto.get_session_key()
        key2 = crypto.get_session_key()

        assert key1 == key2

    def test_session_key_rotation(self):
        """Should rotate session key on demand."""
        crypto = PostQuantumCrypto()
        key1 = crypto.get_session_key()
        key2 = crypto.rotate_session_key()

        assert key1 != key2

    def test_perfect_forward_secrecy(self):
        """Each new session should get new key."""
        crypto = PostQuantumCrypto()
        key1 = crypto.get_session_key()

        crypto2 = PostQuantumCrypto()
        key2 = crypto2.get_session_key()

        # Different instances get different keys (PFS)
        assert key1 != key2


class TestChaCha20Poly1305:
    """Test ChaCha20-Poly1305 AEAD encryption."""

    def test_encrypt_decrypt(self):
        """Should encrypt and decrypt data."""
        crypto = PostQuantumCrypto()
        plaintext = b"Secret message"

        encrypted = crypto.encrypt_chacha20_poly1305(plaintext)
        decrypted = crypto.decrypt_chacha20_poly1305(encrypted)

        assert decrypted == plaintext

    def test_encryption_produces_nonce(self):
        """Each encryption should use unique nonce."""
        crypto = PostQuantumCrypto()
        plaintext = b"Test"

        enc1 = crypto.encrypt_chacha20_poly1305(plaintext)
        enc2 = crypto.encrypt_chacha20_poly1305(plaintext)

        assert enc1.nonce != enc2.nonce

    def test_authenticated_data(self):
        """Should support associated data."""
        crypto = PostQuantumCrypto()
        plaintext = b"Secret"
        aad = b"header_info"

        encrypted = crypto.encrypt_chacha20_poly1305(plaintext, aad)
        decrypted = crypto.decrypt_chacha20_poly1305(encrypted, aad)

        assert decrypted == plaintext

    def test_wrong_aad_fails(self):
        """Wrong AAD should fail decryption."""
        crypto = PostQuantumCrypto()
        plaintext = b"Secret"
        aad = b"header"

        encrypted = crypto.encrypt_chacha20_poly1305(plaintext, aad)
        decrypted = crypto.decrypt_chacha20_poly1305(encrypted, b"wrong_aad")

        assert decrypted is None

    def test_tampering_detection(self):
        """Should detect tampering with ciphertext."""
        crypto = PostQuantumCrypto()
        plaintext = b"Important data"

        encrypted = crypto.encrypt_chacha20_poly1305(plaintext)

        # Tamper with ciphertext
        tampered = bytes([encrypted.ciphertext[0] ^ 0xFF]) + encrypted.ciphertext[1:]
        encrypted.ciphertext = tampered

        decrypted = crypto.decrypt_chacha20_poly1305(encrypted)
        assert decrypted is None


class TestAES256GCM:
    """Test AES-256-GCM AEAD encryption."""

    def test_encrypt_decrypt(self):
        """Should encrypt and decrypt data."""
        crypto = PostQuantumCrypto()
        plaintext = b"Secret message"

        encrypted = crypto.encrypt_aes256_gcm(plaintext)
        decrypted = crypto.decrypt_aes256_gcm(encrypted)

        assert decrypted == plaintext

    def test_unique_nonces(self):
        """Each encryption should use unique nonce."""
        crypto = PostQuantumCrypto()
        plaintext = b"Test"

        enc1 = crypto.encrypt_aes256_gcm(plaintext)
        enc2 = crypto.encrypt_aes256_gcm(plaintext)

        assert enc1.nonce != enc2.nonce

    def test_tampering_detection(self):
        """Should detect tampering."""
        crypto = PostQuantumCrypto()
        plaintext = b"Data"

        encrypted = crypto.encrypt_aes256_gcm(plaintext)
        encrypted.ciphertext = (
            bytes([encrypted.ciphertext[0] ^ 0xFF]) + encrypted.ciphertext[1:]
        )

        decrypted = crypto.decrypt_aes256_gcm(encrypted)
        assert decrypted is None


class TestHashing:
    """Test SHA3 hashing."""

    def test_hash_sha3_256(self):
        """Should hash with SHA3-256."""
        crypto = PostQuantumCrypto()
        data = b"test data"
        hash_result = crypto.hash_sha3_256(data)

        assert len(hash_result) == 32
        assert isinstance(hash_result, bytes)

    def test_hash_sha3_512(self):
        """Should hash with SHA3-512."""
        crypto = PostQuantumCrypto()
        data = b"test data"
        hash_result = crypto.hash_sha3_512(data)

        assert len(hash_result) == 64

    def test_hash_deterministic(self):
        """Same input should produce same hash."""
        crypto = PostQuantumCrypto()
        data = b"test"

        hash1 = crypto.hash_sha3_256(data)
        hash2 = crypto.hash_sha3_256(data)

        assert hash1 == hash2

    def test_hmac_sha3_256(self):
        """Should compute HMAC."""
        crypto = PostQuantumCrypto()
        key = secrets.token_bytes(32)
        data = b"message"

        mac = crypto.hmac_sha3_256(key, data)
        assert len(mac) == 32


class TestKeyDerivation:
    """Test subkey derivation."""

    def test_derive_subkey(self):
        """Should derive subkey from master key."""
        crypto = PostQuantumCrypto()
        subkey = crypto.derive_subkey("encryption")

        assert len(subkey) == 32
        assert isinstance(subkey, bytes)

    def test_derive_different_contexts(self):
        """Different contexts should produce different keys."""
        crypto = PostQuantumCrypto()
        key1 = crypto.derive_subkey("encryption")
        key2 = crypto.derive_subkey("signing")

        assert key1 != key2

    def test_derive_consistent(self):
        """Same context should produce same key."""
        crypto = PostQuantumCrypto()
        key1 = crypto.derive_subkey("auth")
        key2 = crypto.derive_subkey("auth")

        assert key1 == key2


class TestSerialization:
    """Test encryption data serialization."""

    def test_serialize_encrypted(self):
        """Should serialize encrypted data."""
        crypto = PostQuantumCrypto()
        plaintext = b"Test data"
        encrypted = crypto.encrypt_chacha20_poly1305(plaintext)

        serialized = crypto.serialize_encrypted(encrypted)
        assert isinstance(serialized, str)
        assert "alg" in serialized
        assert "c" in serialized  # ciphertext

    def test_roundtrip_serialization(self):
        """Should deserialize correctly."""
        crypto = PostQuantumCrypto()
        plaintext = b"Test data"
        encrypted = crypto.encrypt_chacha20_poly1305(plaintext)

        serialized = crypto.serialize_encrypted(encrypted)
        deserialized = crypto.deserialize_encrypted(serialized)

        assert deserialized.algorithm == encrypted.algorithm
        assert deserialized.nonce == encrypted.nonce
        assert deserialized.ciphertext == encrypted.ciphertext


class TestVerificationFunctions:
    """Test MAC/IP verification."""

    def test_verify_mac_change(self):
        """Should verify MAC address change."""
        record = verify_mac_change("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "wlan0")

        assert record["type"] == "mac_change"
        assert record["interface"] == "wlan0"
        assert "old_mac_hash" in record
        assert "new_mac_hash" in record
        assert record["verified"] is True

    def test_verify_ip_change(self):
        """Should verify IP address change."""
        record = verify_ip_change("192.168.1.100", "10.0.0.50", "wlan0")

        assert record["type"] == "ip_change"
        assert record["interface"] == "wlan0"
        assert "new_ip_hash" in record
        assert record["verified"] is True

    def test_verify_ip_change_no_old_ip(self):
        """Should handle missing old IP."""
        record = verify_ip_change(None, "192.168.1.1", "wlan0")

        assert record["old_ip"] is None
        assert record["verified"] is True


class TestCryptoStatus:
    """Test crypto status reporting."""

    def test_get_status(self):
        """Should return crypto status."""
        crypto = PostQuantumCrypto()
        status = crypto.get_status()

        assert "system" in status
        assert "algorithms" in status
        assert "pfs_enabled" in status
        assert status["pfs_enabled"] is True


class TestGlobalInstance:
    """Test global crypto instance."""

    def test_get_crypto(self):
        """Should return global instance."""
        crypto1 = get_crypto()
        crypto2 = get_crypto()

        assert crypto1 is crypto2
