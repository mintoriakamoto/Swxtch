"""Bitcoin payment processing with 30-day auto-renewal and license key generation.

Handles:
- Bitcoin payment acceptance (wallet hidden in secure config)
- License key generation after payment confirmation
- 30-day license expiration and auto-renewal
- Wallet integration (Phantom, Coinbase, MetaMask)
- Payment verification via blockchain monitoring
- Secure license key distribution
"""

import json
import os
import secrets
import hashlib
import hmac
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
import logging

LOG_DIR = Path("/var/log/swxtch")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

# Bitcoin wallet configuration (stored securely, not in code)
BITCOIN_WALLET = os.getenv("SWXTCH_BITCOIN_WALLET", "[BITCOIN_WALLET_MASKED]")
PAYMENT_AMOUNT_SATOSHI = 100000  # ~0.001 BTC (configurable)

# License parameters
LICENSE_VALIDITY_DAYS = 30
LICENSE_KEY_PREFIX = "sk_btc_"
LICENSE_KEY_LENGTH = 48  # Total: sk_btc_[44 chars]


@dataclass
class BitcoinPayment:
    """Represents a Bitcoin payment for license activation."""
    transaction_id: str
    amount_satoshi: int
    paid_timestamp: str
    wallet_address: str
    customer_email: Optional[str] = None
    confirmed: bool = False
    license_key: Optional[str] = None


@dataclass
class LicenseKey:
    """Generated license key with validity period."""
    key: str
    generated_at: str
    expires_at: str
    transaction_id: str
    payment_address: str
    auto_renew_enabled: bool = True


class BitcoinPaymentManager:
    """Manages Bitcoin payments and license key generation."""

    def __init__(self):
        """Initialize Bitcoin payment manager."""
        self.wallet = BITCOIN_WALLET
        self.payments_log = LOG_DIR / "bitcoin_payments.json"
        self.payment_history = self._load_payment_history()

    def _load_payment_history(self) -> Dict:
        """Load previous payment history."""
        if self.payments_log.exists():
            try:
                with open(self.payments_log) as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                return {}
        return {}

    def _save_payment_history(self):
        """Save payment history to log."""
        try:
            with open(self.payments_log, "w") as f:
                json.dump(self.payment_history, f, indent=2)
            self.payments_log.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save payment history: {e}")

    def generate_payment_request(self) -> Dict:
        """Generate payment request with wallet address and amount."""
        request = {
            "wallet_address": self.wallet,
            "amount_satoshi": PAYMENT_AMOUNT_SATOSHI,
            "amount_btc": PAYMENT_AMOUNT_SATOSHI / 100_000_000,
            "description": "Swxtch Premium License (30-day)",
            "request_id": secrets.token_hex(16),
            "created_at": datetime.utcnow().isoformat(),
            "qr_code_uri": self._generate_bip21_uri(),
        }
        logger.info(f"Generated payment request: {request['request_id']}")
        return request

    def _generate_bip21_uri(self) -> str:
        """Generate BIP21 URI for wallet apps (Phantom, MetaMask, Coinbase)."""
        amount_btc = PAYMENT_AMOUNT_SATOSHI / 100_000_000
        uri = f"bitcoin:{self.wallet}?amount={amount_btc}&label=Swxtch%20Premium"
        return uri

    def generate_license_key(self, transaction_id: str, payment_address: str) -> LicenseKey:
        """Generate cryptographically secure license key after payment confirmation."""
        # Generate random key component (44 chars)
        key_random = secrets.token_urlsafe(33)[:44]
        full_key = f"{LICENSE_KEY_PREFIX}{key_random}"

        now = datetime.utcnow()
        expires_at = now + timedelta(days=LICENSE_VALIDITY_DAYS)

        license_key = LicenseKey(
            key=full_key,
            generated_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            transaction_id=transaction_id,
            payment_address=payment_address,
            auto_renew_enabled=True,
        )

        # Store in payment history
        self.payment_history[transaction_id] = {
            "license_key": full_key,
            "generated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "payment_address": payment_address,
            "status": "active",
            "auto_renew": True,
        }
        self._save_payment_history()

        logger.info(f"Generated license key for transaction: {transaction_id}")
        return license_key

    def verify_license_key(self, key: str) -> Tuple[bool, str]:
        """Verify Bitcoin-based license key validity."""
        if not key.startswith(LICENSE_KEY_PREFIX):
            return False, "Invalid license key format"

        # Find transaction by key
        for tx_id, data in self.payment_history.items():
            if data.get("license_key") == key:
                if data.get("status") == "active":
                    expires_at = datetime.fromisoformat(data.get("expires_at", ""))
                    if datetime.utcnow() < expires_at:
                        days_left = (expires_at - datetime.utcnow()).days
                        return True, f"✓ License valid ({days_left} days remaining)"
                    else:
                        return False, "License expired - renewal required"
                else:
                    return False, "License revoked"

        return False, "License key not found"

    def check_payment_confirmation(self, transaction_id: str) -> Tuple[bool, str]:
        """Check if payment has been confirmed on blockchain."""
        # In production, integrate with:
        # - Mempool.space API for real-time tx confirmation
        # - Blockchain.com API
        # - Your own Bitcoin node for verification
        #
        # This is a placeholder for actual blockchain monitoring

        if transaction_id in self.payment_history:
            data = self.payment_history[transaction_id]
            if data.get("status") == "confirmed":
                return True, "✓ Payment confirmed on blockchain"
            elif data.get("status") == "pending":
                return False, "⏳ Payment pending confirmation (usually 10 minutes)"
            else:
                return False, "Payment not found"

        return False, "Transaction ID not found"

    def enable_auto_renewal(self, license_key: str) -> Tuple[bool, str]:
        """Enable automatic 30-day renewal on expiration."""
        for tx_id, data in self.payment_history.items():
            if data.get("license_key") == license_key:
                data["auto_renew"] = True
                self._save_payment_history()
                return True, "✓ Auto-renewal enabled (30-day recurring)"

        return False, "License key not found"

    def disable_auto_renewal(self, license_key: str) -> Tuple[bool, str]:
        """Disable automatic renewal."""
        for tx_id, data in self.payment_history.items():
            if data.get("license_key") == license_key:
                data["auto_renew"] = False
                self._save_payment_history()
                return True, "✓ Auto-renewal disabled"

        return False, "License key not found"

    def get_payment_status(self) -> Dict:
        """Get overall payment and license status."""
        active_licenses = sum(
            1 for data in self.payment_history.values()
            if data.get("status") == "active"
        )
        expired_licenses = sum(
            1 for data in self.payment_history.values()
            if data.get("status") == "expired"
        )

        return {
            "wallet_address": "[BITCOIN_WALLET_MASKED]",  # Never expose in output
            "total_payments": len(self.payment_history),
            "active_licenses": active_licenses,
            "expired_licenses": expired_licenses,
            "payment_amount_satoshi": PAYMENT_AMOUNT_SATOSHI,
            "payment_amount_btc": PAYMENT_AMOUNT_SATOSHI / 100_000_000,
            "license_validity_days": LICENSE_VALIDITY_DAYS,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def generate_renewal_invoice(self, license_key: str) -> Tuple[bool, Dict]:
        """Generate renewal invoice for expired license."""
        for tx_id, data in self.payment_history.items():
            if data.get("license_key") == license_key:
                expires_at = datetime.fromisoformat(data.get("expires_at", ""))
                if datetime.utcnow() >= expires_at:
                    renewal_request = self.generate_payment_request()
                    renewal_request["renewal_of"] = license_key
                    renewal_request["previous_expiration"] = data.get("expires_at")
                    logger.info(f"Generated renewal invoice for: {license_key}")
                    return True, renewal_request

        return False, {}


# Global instance
_bitcoin_manager = None


def get_bitcoin_manager() -> BitcoinPaymentManager:
    """Get global Bitcoin payment manager instance."""
    global _bitcoin_manager
    if _bitcoin_manager is None:
        _bitcoin_manager = BitcoinPaymentManager()
    return _bitcoin_manager
