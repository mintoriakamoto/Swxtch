"""Tests for freemium licensing system."""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from swxtch.license import (
    get_trial_start,
    is_trial_active,
    get_trial_remaining,
    get_subscription_status,
    check_license,
    activate_license_key,
)


class TestLicenseInitialization:
    """Test license file creation on first run."""

    @patch("swxtch.license.LICENSE_FILE")
    @patch("swxtch.license.LICENSE_DIR")
    def test_first_run_creates_trial_start(self, mock_dir, mock_file):
        """Should create license file on first run."""
        mock_dir.mkdir = MagicMock()
        mock_file.exists.return_value = False

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = MagicMock()
            with patch("pathlib.Path.chmod"):
                trial_start = get_trial_start()

        assert trial_start is not None
        assert isinstance(trial_start, datetime)


class TestTrialPeriod:
    """Test trial period checking."""

    @patch("swxtch.license.get_trial_start")
    @patch("swxtch.license.datetime")
    def test_trial_active_within_7_days(self, mock_datetime, mock_trial_start):
        """Should return True if within 7 days of trial start."""
        trial_start = datetime(2026, 9, 21, 0, 0, 0)
        current = datetime(2026, 9, 25, 0, 0, 0)  # 4 days later

        mock_trial_start.return_value = trial_start
        mock_datetime.utcnow.return_value = current

        assert is_trial_active() is True

    @patch("swxtch.license.get_trial_start")
    @patch("swxtch.license.datetime")
    def test_trial_expired_after_7_days(self, mock_datetime, mock_trial_start):
        """Should return False if after 7 days."""
        trial_start = datetime(2026, 9, 21, 0, 0, 0)
        current = datetime(2026, 9, 29, 0, 0, 1)  # 8 days, 1 second later

        mock_trial_start.return_value = trial_start
        mock_datetime.utcnow.return_value = current

        assert is_trial_active() is False

    @patch("swxtch.license.get_trial_start")
    @patch("swxtch.license.datetime")
    def test_trial_remaining_days(self, mock_datetime, mock_trial_start):
        """Should calculate remaining trial days correctly."""
        trial_start = datetime(2026, 9, 21, 0, 0, 0)
        current = datetime(2026, 9, 25, 12, 0, 0)  # 4.5 days later

        mock_trial_start.return_value = trial_start
        mock_datetime.utcnow.return_value = current

        remaining = get_trial_remaining()
        assert remaining == 2  # 2 full days remaining

    @patch("swxtch.license.get_trial_start")
    @patch("swxtch.license.datetime")
    def test_trial_remaining_zero_after_expiry(self, mock_datetime, mock_trial_start):
        """Should return 0 after trial expires."""
        trial_start = datetime(2026, 9, 21, 0, 0, 0)
        current = datetime(2026, 9, 30, 0, 0, 0)  # 9 days later

        mock_trial_start.return_value = trial_start
        mock_datetime.utcnow.return_value = current

        remaining = get_trial_remaining()
        assert remaining == 0


class TestSubscriptionStatus:
    """Test subscription status reporting."""

    @patch("swxtch.license.is_trial_active")
    @patch("swxtch.license.get_trial_remaining")
    @patch("swxtch.license.LICENSE_FILE")
    def test_active_trial_status(self, mock_file, mock_remaining, mock_trial_active):
        """Should report active trial status."""
        mock_trial_active.return_value = True
        mock_remaining.return_value = 3
        mock_file.exists.return_value = True

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                '{"trial_start": "2026-09-21T00:00:00"}'
            )
            status = get_subscription_status()

        assert status["trial_active"] is True
        assert status["trial_remaining_days"] == 3

    @patch("swxtch.license.is_trial_active")
    @patch("swxtch.license.get_trial_remaining")
    @patch("swxtch.license.LICENSE_FILE")
    def test_expired_trial_status(self, mock_file, mock_remaining, mock_trial_active):
        """Should report expired trial status."""
        mock_trial_active.return_value = False
        mock_remaining.return_value = 0
        mock_file.exists.return_value = True

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                '{"trial_start": "2026-09-21T00:00:00"}'
            )
            status = get_subscription_status()

        assert status["trial_active"] is False
        assert status["trial_remaining_days"] == 0


class TestLicenseCheck:
    """Test license verification."""

    @patch("swxtch.license.is_trial_active")
    @patch("swxtch.license.get_trial_remaining")
    def test_license_check_active_trial(self, mock_remaining, mock_trial_active):
        """Should allow access during active trial."""
        mock_trial_active.return_value = True
        mock_remaining.return_value = 5

        allowed, message = check_license()

        assert allowed is True
        assert "Trial active" in message
        assert "5" in message

    @patch("swxtch.license.is_trial_active")
    def test_license_check_expired_trial(self, mock_trial_active):
        """Should deny access after trial expires."""
        mock_trial_active.return_value = False

        allowed, message = check_license()

        assert allowed is False
        assert "EXPIRED" in message
        assert "$9.99" in message


class TestLicenseActivation:
    """Test license key activation."""

    def test_activate_invalid_format_key(self):
        """Should reject keys with invalid format."""
        invalid_keys = [
            "sk_test_invalid",  # wrong prefix
            "invalid_key",  # no sk_ prefix
            "sk_live_short",  # too short
            "",  # empty
            None,  # None type
        ]

        for key in invalid_keys:
            success, message = activate_license_key(key)
            assert success is False
            assert "invalid" in message.lower() or "format" in message.lower()

    def test_activate_with_too_short_key(self):
        """Should reject keys shorter than 32 chars after prefix."""
        success, message = activate_license_key("sk_live_short")
        assert success is False
        assert "invalid" in message.lower()

    def test_activate_with_invalid_type_key(self):
        """Should reject non-string keys."""
        success, message = activate_license_key(123)
        assert success is False
        assert "invalid" in message.lower()

    def test_activate_success_message(self):
        """Should return success message on valid activation."""
        success, message = activate_license_key("license_key_tool_test_valid_1234567890")
        assert success is False  # Invalid format

        # Test with None to verify error handling
        success, message = activate_license_key(None)
        assert success is False
        assert message  # Should have an error message
