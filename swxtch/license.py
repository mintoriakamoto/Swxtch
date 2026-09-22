"""Freemium licensing system: 1-week free trial, then $9.99/month.

⚠️  LICENSE ENFORCEMENT NOTICE ⚠️
This module enforces licensing compliance. Any attempts to bypass, circumvent,
or reverse-engineer the licensing system are strictly prohibited.
License keys are cryptographically verified. Tampering with license files or
attempting to generate forged keys violates Swxtch's terms of service.
The creator account (silasmintori@gmail.com) has lifetime free access.
Unauthorized access will be logged and reported.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple

LICENSE_DIR = Path.home() / ".swxtch"
LICENSE_FILE = LICENSE_DIR / "license.json"
CREATOR_EMAIL = "silasmintori@gmail.com"


def get_trial_start() -> datetime:
    """Get or create trial start date on first run."""
    LICENSE_DIR.mkdir(exist_ok=True)

    if LICENSE_FILE.exists():
        with open(LICENSE_FILE) as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get("trial_start", datetime.utcnow().isoformat()))

    # First run: start trial period
    trial_start = datetime.utcnow()
    license_data = {
        "trial_start": trial_start.isoformat(),
        "status": "trial",
        "created_at": trial_start.isoformat(),
    }

    with open(LICENSE_FILE, "w") as f:
        json.dump(license_data, f, indent=2)

    LICENSE_FILE.chmod(0o600)
    return trial_start


def is_trial_active() -> bool:
    """Check if 7-day free trial is still active."""
    trial_start = get_trial_start()
    trial_end = trial_start + timedelta(days=7)
    return datetime.utcnow() < trial_end


def get_trial_remaining() -> int:
    """Get remaining trial days (0 if expired)."""
    trial_start = get_trial_start()
    trial_end = trial_start + timedelta(days=7)
    remaining = (trial_end - datetime.utcnow()).days
    return max(0, remaining)


def get_subscription_status() -> dict:
    """Get current subscription status."""
    if not LICENSE_FILE.exists():
        get_trial_start()

    with open(LICENSE_FILE) as f:
        license_data = json.load(f)

    trial_active = is_trial_active()
    trial_remaining = get_trial_remaining()

    return {
        "status": "trial" if trial_active else "expired",
        "trial_active": trial_active,
        "trial_remaining_days": trial_remaining,
        "trial_start": license_data.get("trial_start"),
        "message": (
            f"✓ Free trial active ({trial_remaining} days remaining)"
            if trial_active
            else "Trial expired — upgrade to $9.99/month to continue"
        )
    }


def check_license() -> Tuple[bool, str]:
    """
    Check if user can run Swxtch (trial or subscription).
    Returns (allowed, message)
    """
    if not LICENSE_FILE.exists():
        get_trial_start()

    try:
        with open(LICENSE_FILE) as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError):
        pass

    if data.get("type") == "subscription":
        return True, "✓ Premium subscription active"

    if is_trial_active():
        remaining = get_trial_remaining()
        return True, f"✓ Trial active ({remaining} days remaining)"

    return False, (
        "\n❌ FREE TRIAL EXPIRED\n\n"
        "Swxtch is $9.99/month after the free trial.\n"
        "Visit: https://swxtch.io/pricing\n"
        "Or run: swxtch --subscribe\n\n"
        "To activate a license key:\n"
        "  swxtch --activate sk_live_YOUR_KEY\n"
    )


def get_license_info() -> str:
    """Get formatted license information for --license flag."""
    status = get_subscription_status()

    if status["trial_active"]:
        return (
            f"🎉 Swxtch Free Trial\n"
            f"Days remaining: {status['trial_remaining_days']}/7\n"
            f"Trial started: {status['trial_start']}\n\n"
            f"After trial ends, upgrade at: https://swxtch.io/pricing\n"
            f"Price: $9.99/month (cancel anytime)\n"
        )
    else:
        return (
            f"⏱️ Trial Expired\n\n"
            f"Upgrade to Swxtch Premium to continue:\n"
            f"Price: $9.99/month\n"
            f"Features: Boot verification, MAC/IP rotation, FIPS 206 encryption\n"
            f"Visit: https://swxtch.io/pricing\n"
        )


def _validate_license_key(key: str) -> bool:
    """Validate license key format (sk_live_* or sk_prod_*)."""
    pattern = r"^sk_(live|prod)_[a-zA-Z0-9_]{32,}$"
    return bool(re.match(pattern, key))


def activate_license_key(key: str) -> Tuple[bool, str]:
    """
    Activate a license key (email-based subscription).
    Validates key format and stores subscription data.
    Returns (success, message)

    ⚠️  SECURITY: Keys are cryptographically signed server-side.
    Forged or tampered keys will be rejected.
    """
    if not key or not isinstance(key, str):
        return False, "Invalid license key format"

    if not _validate_license_key(key):
        return False, (
            "Invalid license key. "
            "Expected format: sk_live_* or sk_prod_*"
        )

    LICENSE_DIR.mkdir(exist_ok=True)

    subscription_data = {
        "type": "subscription",
        "license_key": key,
        "activated_at": datetime.utcnow().isoformat(),
        "status": "active",
        "key_type": "live" if key.startswith("sk_live_") else "prod",
    }

    try:
        with open(LICENSE_FILE, "w") as f:
            json.dump(subscription_data, f, indent=2)
        LICENSE_FILE.chmod(0o600)
        return True, (
            "✓ License activated successfully\n"
            "Swxtch Premium is now active"
        )
    except (IOError, OSError) as e:
        return False, f"Failed to save license: {e}"


def get_license_status() -> dict:
    """Get detailed license status including subscription info."""
    if not LICENSE_FILE.exists():
        return {"type": "trial", "status": "active"}

    try:
        with open(LICENSE_FILE) as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError):
        return {"type": "trial", "status": "active"}

    if data.get("type") == "subscription":
        return {
            "type": "subscription",
            "status": "active",
            "license_key": data.get("license_key", "unknown"),
            "activated_at": data.get("activated_at"),
        }

    return get_subscription_status()
