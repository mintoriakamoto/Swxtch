"""Tests for network device primitives."""

import re
from swxtch import netdev


class TestMACGeneration:
    """Test MAC address generation."""

    def test_random_mac_format(self):
        """Generated MAC should be valid hex format."""
        mac = netdev.random_mac()
        # Format: XX:XX:XX:XX:XX:XX
        assert re.match(
            r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", mac
        ), f"Invalid MAC format: {mac}"

    def test_locally_administered_bit(self):
        """First octet should have locally-administered bit set (bit 1 = 1)."""
        for _ in range(100):  # Test multiple generations
            mac = netdev.random_mac()
            first_octet = int(mac.split(":")[0], 16)
            # Bit 1 (locally-administered) should be 1
            assert first_octet & 0x02, f"Locally-administered bit not set in {mac}"

    def test_unicast_bit(self):
        """First octet should have unicast bit set (bit 0 = 0)."""
        for _ in range(100):
            mac = netdev.random_mac()
            first_octet = int(mac.split(":")[0], 16)
            # Bit 0 (multicast) should be 0 for unicast
            assert not (
                first_octet & 0x01
            ), f"Multicast bit set in {mac} (should be unicast)"

    def test_mac_uniqueness(self):
        """Generated MACs should be unique (statistically)."""
        macs = {netdev.random_mac() for _ in range(1000)}
        # Should get 1000 unique MACs (collision probability negligible)
        assert (
            len(macs) == 1000
        ), f"Got {len(macs)} unique MACs out of 1000 (collision detected)"

    def test_mac_randomness(self):
        """Generated MACs should use all 6 octets (not fixed)."""
        macs = [netdev.random_mac() for _ in range(100)]
        octets = [[] for _ in range(6)]

        for mac in macs:
            parts = mac.split(":")
            for i, part in enumerate(parts):
                octets[i].append(int(part, 16))

        # Each octet should have variation (statistical test)
        for i, octet_values in enumerate(octets):
            unique_values = len(set(octet_values))
            # First octet has 6 bits of freedom (2-7), others have 8
            # With 100 samples, expect high variance
            min_unique = 40 if i == 0 else 45
            assert (
                unique_values >= min_unique
            ), f"Octet {i} not random enough: {unique_values} unique values"


class TestMACParsing:
    """Test MAC address parsing and validation."""

    def test_parse_valid_mac(self):
        """Should parse valid MAC addresses."""
        test_macs = [
            "00:11:22:33:44:55",
            "aa:bb:cc:dd:ee:ff",
            "02:00:00:00:00:01",
        ]
        for mac in test_macs:
            parts = mac.split(":")
            assert len(parts) == 6
            for part in parts:
                assert len(part) == 2
                int(part, 16)  # Should not raise

    def test_mac_format_consistency(self):
        """Generated MACs should be consistently formatted."""
        mac = netdev.random_mac()
        parts = mac.split(":")
        assert len(parts) == 6, "MAC should have 6 octets"
        for part in parts:
            assert len(part) == 2, f"Each octet should be 2 chars: {part}"
            assert part == part.lower(), "MAC should be lowercase"
            int(part, 16)  # Should be valid hex


class TestInterfaceDetection:
    """Test Wi-Fi interface detection."""

    def test_list_wifi_interfaces_returns_list(self):
        """Should return a list."""
        result = netdev.list_wifi_interfaces()
        assert isinstance(result, list)

    def test_get_mac_with_invalid_interface(self):
        """Should handle invalid interface gracefully."""
        # Should not raise, but might return None or empty string
        result = netdev.get_mac("nonexistent_interface_xyz123")
        # Result depends on implementation, but shouldn't crash
        assert result is None or isinstance(result, str)


class TestPrivilegeCheck:
    """Test root privilege detection."""

    def test_is_root_returns_bool(self):
        """Should return a boolean."""
        result = netdev.is_root()
        assert isinstance(result, bool)
