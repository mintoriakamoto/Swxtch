"""Tests for Bitcoin payment processing and license key generation."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from swxtch.bitcoin_payments import (
    BitcoinPaymentManager,
    BitcoinPayment,
    LicenseKey,
    get_bitcoin_manager,
)


class TestBitcoinPaymentManager:
    """Test Bitcoin payment manager functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset global instance and payment history before each test."""
        import swxtch.bitcoin_payments
        from pathlib import Path

        swxtch.bitcoin_payments._bitcoin_manager = None

        # Remove payment history file if it exists
        log_dir = Path("/var/log/swxtch")
        payments_log = log_dir / "bitcoin_payments.json"
        if payments_log.exists():
            payments_log.unlink()

        yield

        swxtch.bitcoin_payments._bitcoin_manager = None
        if payments_log.exists():
            payments_log.unlink()

    def test_bitcoin_manager_initialization(self):
        """Test manager initializes with wallet address."""
        mgr = BitcoinPaymentManager()
        assert mgr.wallet == "[BITCOIN_WALLET_MASKED]"
        assert isinstance(mgr.payment_history, dict)

    def test_generate_payment_request(self):
        """Test payment request generation with amount and wallet."""
        mgr = BitcoinPaymentManager()
        request = mgr.generate_payment_request()

        assert request["wallet_address"] == "[BITCOIN_WALLET_MASKED]"
        assert request["amount_satoshi"] == 100000
        assert request["amount_btc"] == pytest.approx(0.001, abs=1e-6)
        assert "request_id" in request
        assert "created_at" in request
        assert "qr_code_uri" in request

    def test_bip21_uri_generation(self):
        """Test BIP21 URI for wallet app compatibility."""
        mgr = BitcoinPaymentManager()
        uri = mgr._generate_bip21_uri()

        assert uri.startswith("bitcoin:")
        assert "[BITCOIN_WALLET_MASKED]" in uri
        assert "amount=0.001" in uri
        assert "label=" in uri

    def test_generate_license_key_format(self):
        """Test license key has correct format and length."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_abc123", "[BITCOIN_WALLET_MASKED]")

        assert isinstance(license_key, LicenseKey)
        assert license_key.key.startswith("sk_btc_")
        assert len(license_key.key) > 10
        assert datetime.fromisoformat(license_key.generated_at) is not None
        assert datetime.fromisoformat(license_key.expires_at) is not None

    def test_license_key_expiration_30_days(self):
        """Test license key expires exactly 30 days after generation."""
        mgr = BitcoinPaymentManager()
        before_gen = datetime.utcnow()
        license_key = mgr.generate_license_key("tx_test", "[BITCOIN_WALLET_MASKED]")
        after_gen = datetime.utcnow()

        expires = datetime.fromisoformat(license_key.expires_at)
        generated = datetime.fromisoformat(license_key.generated_at)

        delta = (expires - generated).days
        assert delta == 30

    def test_verify_active_license_key(self):
        """Test verification of valid, active license key."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_valid", "[BITCOIN_WALLET_MASKED]")

        valid, msg = mgr.verify_license_key(license_key.key)
        assert valid is True
        assert "License valid" in msg
        assert "days remaining" in msg

    def test_verify_invalid_license_key_format(self):
        """Test rejection of incorrectly formatted license keys."""
        mgr = BitcoinPaymentManager()
        valid, msg = mgr.verify_license_key("invalid_key_format")

        assert valid is False
        assert "Invalid license key format" in msg

    def test_verify_nonexistent_license_key(self):
        """Test verification of non-existent license key."""
        mgr = BitcoinPaymentManager()
        valid, msg = mgr.verify_license_key("sk_btc_nonexistentkey123456789")

        assert valid is False
        assert "License key not found" in msg

    def test_verify_expired_license_key(self):
        """Test detection of expired license key."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_expired", "[BITCOIN_WALLET_MASKED]")

        # Manually expire the license
        tx_id = "tx_expired"
        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        mgr.payment_history[tx_id]["expires_at"] = past_time
        mgr._save_payment_history()

        valid, msg = mgr.verify_license_key(license_key.key)
        assert valid is False
        assert "License expired" in msg

    def test_check_payment_pending(self):
        """Test payment pending confirmation status."""
        mgr = BitcoinPaymentManager()
        mgr.payment_history["tx_pending"] = {"status": "pending"}
        mgr._save_payment_history()

        confirmed, msg = mgr.check_payment_confirmation("tx_pending")
        assert confirmed is False
        assert "pending" in msg.lower()

    def test_check_payment_confirmed(self):
        """Test payment confirmed on blockchain."""
        mgr = BitcoinPaymentManager()
        mgr.payment_history["tx_confirmed"] = {"status": "confirmed"}
        mgr._save_payment_history()

        confirmed, msg = mgr.check_payment_confirmation("tx_confirmed")
        assert confirmed is True
        assert "confirmed" in msg.lower()

    def test_check_payment_not_found(self):
        """Test handling of non-existent transaction ID."""
        mgr = BitcoinPaymentManager()
        confirmed, msg = mgr.check_payment_confirmation("tx_nonexistent")

        assert confirmed is False
        assert "not found" in msg.lower()

    def test_enable_auto_renewal(self):
        """Test enabling automatic license renewal."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_renew1", "[BITCOIN_WALLET_MASKED]")

        success, msg = mgr.enable_auto_renewal(license_key.key)
        assert success is True
        assert "Auto-renewal enabled" in msg
        assert mgr.payment_history["tx_renew1"]["auto_renew"] is True

    def test_disable_auto_renewal(self):
        """Test disabling automatic license renewal."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_renew2", "[BITCOIN_WALLET_MASKED]")

        mgr.enable_auto_renewal(license_key.key)
        success, msg = mgr.disable_auto_renewal(license_key.key)
        assert success is True
        assert "Auto-renewal disabled" in msg
        assert mgr.payment_history["tx_renew2"]["auto_renew"] is False

    def test_auto_renewal_not_found(self):
        """Test auto-renewal attempt on non-existent key."""
        mgr = BitcoinPaymentManager()
        success, msg = mgr.enable_auto_renewal("sk_btc_nonexistent")

        assert success is False
        assert "not found" in msg.lower()

    def test_get_payment_status(self):
        """Test overall payment and license status report."""
        mgr = BitcoinPaymentManager()
        mgr.generate_license_key("tx_1", "[BITCOIN_WALLET_MASKED]")
        mgr.generate_license_key("tx_2", "[BITCOIN_WALLET_MASKED]")

        status = mgr.get_payment_status()
        assert status["total_payments"] == 2
        assert status["active_licenses"] == 2
        assert status["payment_amount_satoshi"] == 100000
        assert status["payment_amount_btc"] == pytest.approx(0.001, abs=1e-6)
        assert status["license_validity_days"] == 30
        assert "[BITCOIN_WALLET_MASKED]" in status["wallet_address"]

    def test_generate_renewal_invoice(self):
        """Test generation of renewal invoice for expired license."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_renewal", "[BITCOIN_WALLET_MASKED]")

        # Expire the license
        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        mgr.payment_history["tx_renewal"]["expires_at"] = past_time
        mgr._save_payment_history()

        success, invoice = mgr.generate_renewal_invoice(license_key.key)
        assert success is True
        assert "renewal_of" in invoice
        assert invoice["renewal_of"] == license_key.key
        assert "previous_expiration" in invoice

    def test_renewal_invoice_not_expired(self):
        """Test that renewal invoice cannot be generated for active license."""
        mgr = BitcoinPaymentManager()
        license_key = mgr.generate_license_key("tx_active", "[BITCOIN_WALLET_MASKED]")

        success, invoice = mgr.generate_renewal_invoice(license_key.key)
        assert success is False
        assert invoice == {}

    def test_multiple_license_keys_independent(self):
        """Test that multiple license keys are tracked independently."""
        mgr = BitcoinPaymentManager()
        key1 = mgr.generate_license_key("tx_1", "[BITCOIN_WALLET_MASKED]")
        key2 = mgr.generate_license_key("tx_2", "[BITCOIN_WALLET_MASKED]")

        assert key1.key != key2.key
        assert key1.transaction_id != key2.transaction_id

        valid1, _ = mgr.verify_license_key(key1.key)
        valid2, _ = mgr.verify_license_key(key2.key)
        assert valid1 is True
        assert valid2 is True

    def test_payment_history_persistence(self):
        """Test payment history is saved and loaded correctly."""
        mgr1 = BitcoinPaymentManager()
        key1 = mgr1.generate_license_key("tx_persist", "[BITCOIN_WALLET_MASKED]")

        # Create new manager instance (simulates restart)
        import swxtch.bitcoin_payments
        swxtch.bitcoin_payments._bitcoin_manager = None
        mgr2 = get_bitcoin_manager()

        # Verify key is still valid in new instance
        valid, msg = mgr2.verify_license_key(key1.key)
        assert valid is True

    def test_get_bitcoin_manager_singleton(self):
        """Test that get_bitcoin_manager returns singleton instance."""
        mgr1 = get_bitcoin_manager()
        mgr2 = get_bitcoin_manager()

        assert mgr1 is mgr2

    def test_wallet_address_masked_in_output(self):
        """Test that real wallet address is never exposed in status output."""
        mgr = BitcoinPaymentManager()
        status = mgr.get_payment_status()

        # Should show masked version, not real address
        assert status["wallet_address"] == "[BITCOIN_WALLET_MASKED]"

    def test_license_key_uniqueness(self):
        """Test that each generated license key is unique."""
        mgr = BitcoinPaymentManager()
        keys = set()

        for i in range(10):
            key = mgr.generate_license_key(f"tx_{i}", "[BITCOIN_WALLET_MASKED]")
            keys.add(key.key)

        assert len(keys) == 10, "All keys should be unique"

    def test_license_key_randomness(self):
        """Test that license keys are cryptographically random."""
        mgr = BitcoinPaymentManager()
        keys = []

        for i in range(5):
            key = mgr.generate_license_key(f"tx_random_{i}", "[BITCOIN_WALLET_MASKED]")
            keys.append(key.key)

        # Each key should have different random component
        random_components = [k.replace("sk_btc_", "") for k in keys]
        assert len(set(random_components)) == 5

    def test_payment_history_encryption(self):
        """Test that payment history is encrypted at rest."""
        import os
        mgr = BitcoinPaymentManager()
        key = mgr.generate_license_key("tx_encrypt_test", "[BITCOIN_WALLET_MASKED]")

        # Get the saved file content
        if mgr.payments_log.exists():
            with open(mgr.payments_log, "r") as f:
                file_content = f.read()

            # Encrypted content should NOT contain readable JSON
            assert "{" not in file_content or "license_key" not in file_content, \
                "File content should be encrypted, not plain JSON"
            assert "sk_btc_" not in file_content, \
                "License key should not be readable in encrypted file"

    def test_encrypted_data_decryption(self):
        """Test that encrypted data can be decrypted correctly."""
        mgr = BitcoinPaymentManager()
        test_data = "{'test': 'value'}"

        encrypted = mgr._encrypt_data(test_data)
        decrypted = mgr._decrypt_data(encrypted)

        assert decrypted == test_data, "Decrypted data should match original"
        assert encrypted != test_data, "Encrypted data should differ from original"

    def test_encryption_key_derivation(self):
        """Test that encryption key is derived from wallet address."""
        mgr1 = BitcoinPaymentManager()
        mgr2 = BitcoinPaymentManager()

        # Same wallet should produce same cipher suite
        test_data = "sensitive_payment_data"
        encrypted1 = mgr1._encrypt_data(test_data)
        decrypted2 = mgr2._decrypt_data(encrypted1)

        assert decrypted2 == test_data, \
            "Same wallet address should decrypt data encrypted by another instance"

    def test_wrong_wallet_cannot_decrypt(self):
        """Test that wrong wallet address cannot decrypt payment history."""
        from unittest.mock import MagicMock
        from cryptography.fernet import InvalidToken

        mgr1 = BitcoinPaymentManager()
        test_data = "{'sensitive': 'payment_data'}"
        encrypted = mgr1._encrypt_data(test_data)

        # Create a manager with a different wallet
        mgr2 = BitcoinPaymentManager()
        mgr2.wallet = "bc1qDIFFERENT_WALLET"
        mgr2._cipher_suite = mgr2._derive_cipher_suite()

        # Try to decrypt with wrong wallet - should fail or return empty
        decrypted = mgr2._decrypt_data(encrypted)
        assert decrypted == "", "Wrong wallet should fail to decrypt data"

    def test_payment_persistence_with_encryption(self):
        """Test that payment history persists correctly with encryption."""
        mgr1 = BitcoinPaymentManager()
        key1 = mgr1.generate_license_key("tx_persist_encrypt", "[BITCOIN_WALLET_MASKED]")

        # Create new manager instance (simulates restart)
        import swxtch.bitcoin_payments
        swxtch.bitcoin_payments._bitcoin_manager = None
        mgr2 = BitcoinPaymentManager()

        # Verify encrypted data was persisted and decrypted correctly
        assert "tx_persist_encrypt" in mgr2.payment_history
        stored_key = mgr2.payment_history["tx_persist_encrypt"]["license_key"]
        assert stored_key == key1.key, "License key should be preserved through encryption/decryption"

    def test_encryption_prevents_tampering(self):
        """Test that encrypted file cannot be tampered with."""
        mgr = BitcoinPaymentManager()
        key = mgr.generate_license_key("tx_tamper", "[BITCOIN_WALLET_MASKED]")

        # Save original
        mgr._save_payment_history()

        # Try to tamper with the encrypted file
        with open(mgr.payments_log, "r") as f:
            encrypted_content = f.read()

        # Corrupt the encrypted data
        tampered_content = encrypted_content[:-10] + "corrupted!"

        with open(mgr.payments_log, "w") as f:
            f.write(tampered_content)

        # Try to load tampered data
        import swxtch.bitcoin_payments
        swxtch.bitcoin_payments._bitcoin_manager = None
        mgr_tampered = BitcoinPaymentManager()

        # Should return empty dict due to decryption failure
        assert len(mgr_tampered.payment_history) == 0, \
            "Tampered encrypted data should fail to decrypt"
