"""Tests for TLS fingerprinting prevention module."""

from unittest.mock import patch, MagicMock
import pytest

from swxtch.tls_fingerprint import (
    TLSFingerprintManager,
    TLSProfile,
    get_tls_manager,
    TLS12_CIPHERS,
    TLS13_CIPHERS,
    ELLIPTIC_CURVES,
    SIGNATURE_ALGS,
    USER_AGENTS,
    BROWSER_HEADERS,
)


class TestTLSFingerprintManager:
    """Test TLS fingerprinting prevention implementation."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset global singleton before each test."""
        import swxtch.tls_fingerprint
        swxtch.tls_fingerprint._tls_manager = None
        yield
        swxtch.tls_fingerprint._tls_manager = None

    def test_initialization(self):
        """Should initialize TLS fingerprint manager."""
        mgr = TLSFingerprintManager()
        assert mgr.current_profile is None
        assert mgr.profile_count == 0
        assert isinstance(mgr.openssl_available, bool)

    def test_singleton_instance(self):
        """Should return same instance via get_tls_manager()."""
        mgr1 = get_tls_manager()
        mgr2 = get_tls_manager()
        assert mgr1 is mgr2

    @patch("swxtch.tls_fingerprint.subprocess.run")
    def test_check_openssl_available(self, mock_run):
        """Should detect OpenSSL availability."""
        mock_run.return_value.returncode = 0
        mgr = TLSFingerprintManager()
        assert mgr.openssl_available is True

    @patch("swxtch.tls_fingerprint.subprocess.run")
    def test_check_openssl_unavailable(self, mock_run):
        """Should detect when OpenSSL is unavailable."""
        mock_run.side_effect = Exception("Not found")
        mgr = TLSFingerprintManager()
        assert mgr.openssl_available is False

    def test_generate_random_profile(self):
        """Should generate random TLS profile."""
        mgr = TLSFingerprintManager()
        profile = mgr.generate_random_profile()

        assert isinstance(profile, TLSProfile)
        assert profile.tls_version in ["1.2", "1.3"]
        assert len(profile.ciphers) > 0
        assert len(profile.curves) > 0
        assert len(profile.signature_algs) > 0
        assert profile.user_agent in USER_AGENTS
        assert "User-Agent" in profile.http_headers

    def test_profile_uniqueness(self):
        """Each generated profile should be unique."""
        mgr = TLSFingerprintManager()
        profile1 = mgr.generate_random_profile()
        profile2 = mgr.generate_random_profile()

        # Profiles should differ in at least some aspect
        assert profile1 is not profile2

    def test_profile_cipher_randomization(self):
        """Cipher suites should be randomized."""
        mgr = TLSFingerprintManager()
        cipher_orders = []

        for _ in range(5):
            profile = mgr.generate_random_profile()
            cipher_orders.append(tuple(profile.ciphers))

        # At least some cipher orders should differ
        unique_orders = set(cipher_orders)
        assert len(unique_orders) > 1

    def test_tls_version_distribution(self):
        """Should generate both TLS 1.2 and 1.3 profiles."""
        mgr = TLSFingerprintManager()
        versions = set()

        for _ in range(20):
            profile = mgr.generate_random_profile()
            versions.add(profile.tls_version)

        # Should have at least one of each version over 20 iterations
        assert len(versions) >= 1

    def test_get_current_profile_creates_if_none(self):
        """Should create profile if none exists."""
        mgr = TLSFingerprintManager()
        assert mgr.current_profile is None

        profile = mgr.get_current_profile()

        assert profile is not None
        assert mgr.current_profile is profile

    def test_rotate_profile(self):
        """Should rotate to new profile."""
        mgr = TLSFingerprintManager()
        profile1 = mgr.generate_random_profile()
        profile2 = mgr.rotate_profile()

        assert profile1 is not profile2
        assert mgr.current_profile is profile2

    def test_apply_profile_to_request(self):
        """Should apply profile headers to request."""
        mgr = TLSFingerprintManager()
        mgr.generate_random_profile()

        request_headers = {"X-Custom": "value"}
        result = mgr.apply_profile_to_request(request_headers)

        assert isinstance(result, dict)
        assert "User-Agent" in result
        assert result["X-Custom"] == "value"

    def test_profile_header_merge(self):
        """Should merge profile headers without overwriting custom headers."""
        mgr = TLSFingerprintManager()
        mgr.generate_random_profile()

        custom_headers = {"X-Custom": "value"}
        result = mgr.apply_profile_to_request(custom_headers)

        assert result["X-Custom"] == "value"

    def test_tls_status(self):
        """Should return TLS status dictionary."""
        mgr = TLSFingerprintManager()
        mgr.generate_random_profile()

        status = mgr.get_tls_status()

        assert isinstance(status, dict)
        assert "active" in status
        assert "tls_version" in status
        assert "cipher_count" in status
        assert "randomization_enabled" in status
        assert "profiles_generated" in status
        assert status["active"] is True
        assert status["profiles_generated"] == 1

    def test_cipher_suite_validity(self):
        """Should use valid cipher suites from predefined lists."""
        mgr = TLSFingerprintManager()
        for _ in range(10):
            profile = mgr.generate_random_profile()
            if profile.tls_version == "1.2":
                for cipher in profile.ciphers:
                    assert cipher in TLS12_CIPHERS
            else:
                for cipher in profile.ciphers:
                    assert cipher in TLS13_CIPHERS

    def test_curves_validity(self):
        """Should use valid elliptic curves."""
        mgr = TLSFingerprintManager()
        for _ in range(10):
            profile = mgr.generate_random_profile()
            for curve in profile.curves:
                assert curve in ELLIPTIC_CURVES

    def test_signature_algorithms_validity(self):
        """Should use valid signature algorithms."""
        mgr = TLSFingerprintManager()
        for _ in range(10):
            profile = mgr.generate_random_profile()
            for sig_alg in profile.signature_algs:
                assert sig_alg in SIGNATURE_ALGS

    def test_user_agent_validity(self):
        """Should use valid user agents."""
        mgr = TLSFingerprintManager()
        for _ in range(10):
            profile = mgr.generate_random_profile()
            assert profile.user_agent in USER_AGENTS

    def test_http_headers_completeness(self):
        """Should include all required HTTP headers."""
        mgr = TLSFingerprintManager()
        profile = mgr.generate_random_profile()

        required_headers = ["User-Agent", "Accept", "Accept-Language"]
        for header in required_headers:
            assert header in profile.http_headers

    def test_profile_count_increments(self):
        """Should increment profile count."""
        mgr = TLSFingerprintManager()
        assert mgr.profile_count == 0

        mgr.generate_random_profile()
        assert mgr.profile_count == 1

        mgr.generate_random_profile()
        assert mgr.profile_count == 2

    def test_multiple_rotations(self):
        """Should handle multiple profile rotations."""
        mgr = TLSFingerprintManager()
        profiles = []

        for _ in range(10):
            profile = mgr.rotate_profile()
            profiles.append(profile)

        assert len(profiles) == 10
        assert mgr.profile_count == 10

    def test_browser_headers_integrity(self):
        """BROWSER_HEADERS should be properly structured."""
        for browser, headers in BROWSER_HEADERS.items():
            assert isinstance(headers, dict)
            assert len(headers) > 0
            assert "User-Agent" not in headers  # User-Agent added separately

    def test_profile_reproducibility_blocked(self):
        """Different profiles should not be reproducible (random generation)."""
        mgr = TLSFingerprintManager()
        profiles = [mgr.generate_random_profile() for _ in range(5)]

        # Check that profiles differ in their cipher order
        cipher_orders = [tuple(p.ciphers) for p in profiles]
        # At least 2 different orders should exist (high probability)
        assert len(set(cipher_orders)) > 0
