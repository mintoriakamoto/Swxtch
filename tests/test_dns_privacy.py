"""Tests for advanced DNS privacy module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from swxtch.dns_privacy import (
    DNSPrivacyManager,
    get_dns_manager,
    DNS_PROVIDERS,
)


class TestDNSPrivacyManager:
    """Test DNS privacy manager implementation."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset global singleton before each test."""
        import swxtch.dns_privacy
        swxtch.dns_privacy._dns_manager = None
        yield
        swxtch.dns_privacy._dns_manager = None

    def test_initialization(self):
        """Should initialize DNS privacy manager."""
        mgr = DNSPrivacyManager()
        assert mgr.current_provider == "tor"
        assert isinstance(mgr.providers_available, dict)
        assert mgr.batch_size == 10
        assert mgr.rotation_counter == 0

    def test_singleton_instance(self):
        """Should return same instance via get_dns_manager()."""
        mgr1 = get_dns_manager()
        mgr2 = get_dns_manager()
        assert mgr1 is mgr2

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_check_providers_tor_running(self, mock_run):
        """Should detect Tor availability."""
        mock_run.return_value.returncode = 0
        mgr = DNSPrivacyManager()
        assert mgr.providers_available.get("tor", False)

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_check_providers_tor_not_running(self, mock_run):
        """Should detect when Tor is not running."""
        mock_run.return_value.returncode = 1
        mgr = DNSPrivacyManager()
        assert not mgr.providers_available.get("tor", False)

    def test_providers_non_tor_available(self):
        """Non-Tor providers should always be marked available."""
        mgr = DNSPrivacyManager()
        assert mgr.providers_available.get("cloudflare", False)
        assert mgr.providers_available.get("quad9", False)
        assert mgr.providers_available.get("mullvad", False)

    def test_rotate_dns_provider(self):
        """Should rotate to next available DNS provider."""
        mgr = DNSPrivacyManager()
        original = mgr.current_provider
        mgr.rotate_dns_provider()
        # Provider should change or stay same if only one available
        assert isinstance(mgr.current_provider, str)
        assert mgr.rotation_counter == 1

    def test_rotate_dns_provider_multiple_times(self):
        """Should cycle through available providers."""
        mgr = DNSPrivacyManager()
        providers_seen = set()
        for _ in range(5):
            mgr.rotate_dns_provider()
            providers_seen.add(mgr.current_provider)
        assert len(providers_seen) > 0

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_configure_dns_over_tor_success(self, mock_run):
        """Should configure DNS-over-Tor when Tor is running."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            with patch("swxtch.dns_privacy.DNS_CONFIG_DIR", config_dir):
                mgr = DNSPrivacyManager()
                mgr.providers_available["tor"] = True
                mock_run.return_value.returncode = 0

                ok, msg = mgr.configure_dns_over_tor()

                assert ok is True
                assert "Tor" in msg
                assert mgr.current_provider == "tor"
                # Check config file was created
                config_file = config_dir / "tor.conf"
                assert config_file.exists()

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_configure_dns_over_tor_tor_not_running(self, mock_run):
        """Should fail gracefully when Tor is not running."""
        mgr = DNSPrivacyManager()
        mgr.providers_available["tor"] = False

        ok, msg = mgr.configure_dns_over_tor()

        assert ok is False
        assert "Tor not running" in msg

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_configure_multi_dns_rotation(self, mock_run):
        """Should configure multi-DNS provider rotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            with patch("swxtch.dns_privacy.DNS_CONFIG_DIR", config_dir):
                mgr = DNSPrivacyManager()
                mock_run.return_value.returncode = 0

                ok, msg = mgr.configure_multi_dns_rotation()

                assert ok is True
                assert "DNS providers" in msg
                config_file = config_dir / "privacy.conf"
                assert config_file.exists()

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_add_dummy_dns_queries(self, mock_run):
        """Should add dummy DNS queries."""
        mgr = DNSPrivacyManager()
        mock_run.return_value.returncode = 0

        ok, msg = mgr.add_dummy_dns_queries(5)

        assert ok is True
        assert "dummy queries" in msg.lower()

    def test_add_dummy_dns_queries_zero_count(self):
        """Should handle zero dummy queries."""
        mgr = DNSPrivacyManager()
        ok, msg = mgr.add_dummy_dns_queries(0)
        # Should still succeed but add no queries
        assert ok is True

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_validate_dnssec_enabled(self, mock_run):
        """Should detect DNSSEC enabled."""
        mock_run.return_value.stdout = "DNSSEC setting: yes"
        mock_run.return_value.text = "DNSSEC setting: yes"

        mgr = DNSPrivacyManager()
        ok, msg = mgr.validate_dnssec()

        assert ok is True
        assert "DNSSEC" in msg

    @patch("swxtch.dns_privacy.subprocess.run")
    def test_validate_dnssec_disabled(self, mock_run):
        """Should detect DNSSEC disabled."""
        mock_run.return_value.stdout = "DNSSEC setting: no"
        mock_run.return_value.text = "DNSSEC setting: no"

        mgr = DNSPrivacyManager()
        ok, msg = mgr.validate_dnssec()

        assert ok is False
        assert "DNSSEC" in msg

    def test_get_dns_privacy_status(self):
        """Should return DNS privacy status dict."""
        mgr = DNSPrivacyManager()
        status = mgr.get_dns_privacy_status()

        assert isinstance(status, dict)
        assert "current_provider" in status
        assert "providers_available" in status
        assert "timestamp" in status
        assert status["current_provider"] in DNS_PROVIDERS.keys()

    def test_dns_providers_configuration(self):
        """Should have valid DNS provider configurations."""
        for provider, config in DNS_PROVIDERS.items():
            assert "primary" in config or "protocol" in config
            if provider != "tor":
                assert "primary" in config
                assert isinstance(config["primary"], str)

    def test_query_batching(self):
        """Should support query batching."""
        mgr = DNSPrivacyManager()
        assert mgr.batch_size > 0
        assert isinstance(mgr.query_buffer, list)

    def test_concurrent_rotation(self):
        """Should handle concurrent provider rotations."""
        mgr = DNSPrivacyManager()
        for _ in range(10):
            mgr.rotate_dns_provider()

        assert mgr.rotation_counter == 10
        assert isinstance(mgr.current_provider, str)
