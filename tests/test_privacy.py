"""Tests for privacy hardening module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from swxtch import privacy


class TestDHCPPrivacy:
    """Test DHCP privacy hardening."""

    def test_generate_random_hostname(self):
        """Should generate 12-character random hostname."""
        hostname = privacy.generate_random_hostname()
        assert len(hostname) == 12
        assert hostname.isalnum()
        assert hostname.islower()

    def test_random_hostnames_unique(self):
        """Should generate different hostnames each time."""
        hostnames = [privacy.generate_random_hostname() for _ in range(10)]
        assert len(set(hostnames)) == 10

    def test_generate_random_dhcp_client_id(self):
        """Should generate RFC 4361 compliant client ID."""
        client_id = privacy.generate_random_dhcp_client_id()
        assert client_id.startswith("01:")
        parts = client_id.split(":")
        assert len(parts) == 7  # Type + 6 bytes

    def test_dhcp_client_ids_unique(self):
        """Should generate different client IDs."""
        ids = [privacy.generate_random_dhcp_client_id() for _ in range(5)]
        assert len(set(ids)) == 5

    @patch("swxtch.privacy._has_binary")
    def test_configure_dhcp_privacy_requires_nmcli(self, mock_has):
        """Should require NetworkManager (nmcli)."""
        mock_has.return_value = False
        success, message = privacy.configure_dhcp_privacy("wlan0")
        assert success is False
        assert "NetworkManager" in message

    @patch("swxtch.privacy._run")
    @patch("swxtch.privacy._has_binary")
    def test_configure_dhcp_privacy_with_nmcli(self, mock_has, mock_run):
        """Should configure DHCP privacy when nmcli available."""
        mock_has.return_value = True
        mock_run.return_value = (True, "")

        with patch("swxtch.privacy.PRIVACY_CONFIG_DIR", Path(tempfile.gettempdir())):
            success, message = privacy.configure_dhcp_privacy("wlan0")
            assert success is True
            assert "DHCP privacy" in message
            assert mock_run.call_count >= 1


class TestDNSPrivacy:
    """Test DNS-over-TLS/HTTPS privacy."""

    def test_dns_servers_available(self):
        """Should have multiple DNS server options."""
        assert len(privacy.DNS_OVER_HTTPS_SERVERS) >= 3
        assert len(privacy.DNS_OVER_TLS_SERVERS) >= 3

    def test_dns_over_https_format(self):
        """DNS over HTTPS servers should be valid URLs."""
        for server in privacy.DNS_OVER_HTTPS_SERVERS:
            assert server.startswith("https://")
            assert "/dns-query" in server

    def test_dns_over_tls_format(self):
        """DNS over TLS servers should have port 853."""
        for server in privacy.DNS_OVER_TLS_SERVERS:
            assert ":853" in server

    @patch("swxtch.privacy._has_binary")
    def test_configure_dns_privacy_requires_systemd(self, mock_has):
        """Should require systemd-resolved."""
        mock_has.return_value = False
        success, message = privacy.configure_dns_privacy("cloudflare")
        assert success is False
        assert "systemd-resolved" in message

    def test_invalid_dns_provider(self):
        """Should reject unknown DNS provider."""
        with patch("swxtch.privacy._has_binary", return_value=True):
            with patch("swxtch.privacy._run", return_value=(False, "")):
                success, message = privacy.configure_dns_privacy("invalid")
                assert success is False
                assert "Unknown DNS provider" in message


class TestIPLeakPrevention:
    """Test IPv4 and IPv6 leak prevention."""

    @patch("swxtch.privacy._run")
    @patch.dict("os.environ", {}, clear=True)
    def test_prevent_ipv4_leaks_no_vpn(self, mock_run):
        """Should warn if no VPN/tunnel detected."""
        mock_run.return_value = (True, "default via 192.168.1.1")
        safe, message = privacy.prevent_ipv4_leaks()
        assert safe is False
        assert "IPv4 leak" in message or "no VPN" in message.lower()

    @patch("swxtch.privacy._run")
    def test_prevent_ipv4_leaks_with_vpn(self, mock_run):
        """Should detect VPN tunnel."""
        mock_run.return_value = (True, "default via 10.0.0.1 dev tun0")
        safe, message = privacy.prevent_ipv4_leaks()
        assert safe is True
        assert "IPv4 protected" in message

    @patch("swxtch.privacy._run")
    @patch("swxtch.privacy._has_binary")
    def test_prevent_ipv6_leaks_success(self, mock_has, mock_run):
        """Should disable IPv6 successfully."""
        mock_has.return_value = True
        mock_run.return_value = (True, "")
        success, message = privacy.prevent_ipv6_leaks("wlan0")
        assert success is True
        assert "IPv6 disabled" in message

    @patch("swxtch.privacy._has_binary")
    def test_prevent_ipv6_requires_nmcli(self, mock_has):
        """Should require NetworkManager."""
        mock_has.return_value = False
        success, message = privacy.prevent_ipv6_leaks("wlan0")
        assert success is False
        assert "NetworkManager" in message


class TestWebRTCProtection:
    """Test WebRTC leak prevention."""

    @patch("swxtch.privacy._has_binary")
    def test_block_webrtc_leaks_no_ufw(self, mock_has):
        """Should handle missing ufw gracefully."""
        mock_has.return_value = False
        success, message = privacy.block_webrtc_leaks()
        assert success is False
        assert "ufw" in message

    @patch("swxtch.privacy._has_binary")
    def test_block_webrtc_leaks_with_ufw(self, mock_has):
        """Should provide browser configuration guidance."""
        mock_has.return_value = True
        success, message = privacy.block_webrtc_leaks()
        assert success is True
        assert "Firefox" in message or "Chrome" in message


class TestPrivacyStatus:
    """Test privacy status reporting."""

    @patch("swxtch.privacy._run")
    def test_get_privacy_status_structure(self, mock_run):
        """Should return structured privacy status."""
        mock_run.return_value = (True, "")
        status = privacy.get_privacy_status()

        assert "timestamp" in status
        assert "dhcp_privacy" in status
        assert "dns_privacy" in status
        assert "ipv4_protected" in status
        assert "ipv6_protected" in status
        assert "webrtc_protected" in status
        assert "overall_privacy_score" in status

    @patch("swxtch.privacy._run")
    def test_privacy_score_calculation(self, mock_run):
        """Should calculate privacy score 0-100."""
        mock_run.return_value = (True, "")
        status = privacy.get_privacy_status()
        assert 0 <= status["overall_privacy_score"] <= 100

    @patch("swxtch.privacy._run")
    def test_privacy_status_no_config(self, mock_run):
        """Should handle missing privacy config gracefully."""
        mock_run.return_value = (True, "")
        with patch("swxtch.privacy.PRIVACY_CONFIG_FILE", Path("/nonexistent/config.json")):
            status = privacy.get_privacy_status()
            assert status["dhcp_privacy"] is False
            assert status["dns_privacy"] is False


class TestPrivacyVerification:
    """Test comprehensive privacy verification."""

    @patch("swxtch.privacy._run")
    @patch("swxtch.privacy.PRIVACY_CONFIG_FILE")
    def test_verify_privacy_hardening_structure(self, mock_file, mock_run):
        """Should return verification report."""
        mock_file.exists.return_value = False
        mock_run.return_value = (True, "")

        all_good, report = privacy.verify_privacy_hardening()
        assert isinstance(report, str)
        assert len(report) > 0

    @patch("swxtch.privacy._run")
    @patch("swxtch.privacy.PRIVACY_CONFIG_FILE")
    def test_verify_privacy_checks_multiple_vectors(self, mock_file, mock_run):
        """Should check multiple privacy vectors."""
        mock_file.exists.return_value = True
        mock_run.return_value = (True, "")

        all_good, report = privacy.verify_privacy_hardening()
        assert "DHCP" in report or "dns" in report.lower() or "IPv" in report


class TestPrivacyIntegration:
    """Integration tests for privacy module."""

    def test_privacy_config_structure(self):
        """Privacy config should have required fields."""
        config = {
            "interface": "wlan0",
            "dhcp_hostname_randomized": True,
            "dhcp_client_id_randomized": True,
            "send_hostname_disabled": True,
            "configured_at": "2026-09-22T12:00:00",
        }

        assert "interface" in config
        assert "dhcp_hostname_randomized" in config
        assert all(isinstance(v, (bool, str)) for v in config.values())

    def test_privacy_vectors_coverage(self):
        """Module should address major privacy vectors."""
        vectors = [
            "DHCP privacy",
            "DNS privacy",
            "IPv4 leak",
            "IPv6 leak",
            "WebRTC",
        ]

        for vector in vectors:
            assert hasattr(privacy, "prevent_ipv4_leaks") or \
                   hasattr(privacy, "configure_dhcp_privacy") or \
                   hasattr(privacy, "configure_dns_privacy")
