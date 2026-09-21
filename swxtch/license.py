"""Freemium licensing system: 1-week free trial, then $9.99/month."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

LICENSE_DIR = Path.home() / ".swxtch"
LICENSE_FILE = LICENSE_DIR / "license.json"


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


def check_license() -> tuple[bool, str]:
    """
    Check if user can run Swxtch.
    Returns (allowed, message)
    """
    if is_trial_active():
        remaining = get_trial_remaining()
        return True, f"✓ Trial active ({remaining} days remaining)"
    else:
        return False, (
            "\n❌ FREE TRIAL EXPIRED\n\n"
            "Swxtch is $9.99/month after the free trial.\n"
            "Visit: https://swxtch.io/pricing\n"
            "Or run: swxtch --subscribe\n"
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
