"""Tests for traffic analysis prevention module."""

from unittest.mock import patch, MagicMock
import pytest

from swxtch.traffic_analysis import (
    TrafficAnalysisManager,
    TrafficShapingConfig,
    get_traffic_manager,
    CONSTANT_RATES,
    PADDING_SIZES,
)


class TestTrafficAnalysisManager:
    """Test traffic analysis prevention implementation."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset global singleton before each test."""
        import swxtch.traffic_analysis

        swxtch.traffic_analysis._traffic_manager = None
        yield
        swxtch.traffic_analysis._traffic_manager = None

    def test_initialization(self):
        """Should initialize traffic analysis manager."""
        mgr = TrafficAnalysisManager()
        assert isinstance(mgr.config, TrafficShapingConfig)
        assert mgr.config.bitrate_kbps == 256
        assert mgr.config.packet_padding is True
        assert mgr.packets_sent == 0
        assert mgr.bytes_padded == 0

    def test_singleton_instance(self):
        """Should return same instance via get_traffic_manager()."""
        mgr1 = get_traffic_manager()
        mgr2 = get_traffic_manager()
        assert mgr1 is mgr2

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_check_tc_available(self, mock_run):
        """Should detect tc availability."""
        mock_run.return_value.returncode = 0
        mgr = TrafficAnalysisManager()
        assert mgr.tc_available is True

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_check_tc_unavailable(self, mock_run):
        """Should detect when tc is unavailable."""
        mock_run.side_effect = Exception("Not found")
        mgr = TrafficAnalysisManager()
        assert mgr.tc_available is False

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_enable_constant_bitrate_success(self, mock_run):
        """Should enable constant bitrate successfully."""
        mock_run.return_value.returncode = 0
        mgr = TrafficAnalysisManager()

        ok, msg = mgr.enable_constant_bitrate("wlan0", 256)

        assert ok is True
        assert "Traffic shaping" in msg
        assert mgr.config.bitrate_kbps == 256

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_enable_constant_bitrate_failure(self, mock_run):
        """Should handle constant bitrate failure."""
        mock_run.side_effect = Exception("Permission denied")
        mgr = TrafficAnalysisManager()
        mgr.tc_available = True

        ok, msg = mgr.enable_constant_bitrate("wlan0", 256)

        assert ok is False

    def test_enable_constant_bitrate_tc_unavailable(self):
        """Should fail gracefully when tc unavailable."""
        mgr = TrafficAnalysisManager()
        with patch.object(mgr, "_check_tc", return_value=False):
            ok, msg = mgr.enable_constant_bitrate("wlan0", 256)

        assert ok is False
        assert "not available" in msg

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_disable_traffic_shaping_success(self, mock_run):
        """Should disable traffic shaping."""
        mock_run.return_value.returncode = 0
        mgr = TrafficAnalysisManager()

        ok, msg = mgr.disable_traffic_shaping("wlan0")

        assert ok is True
        assert "disabled" in msg.lower()

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_disable_traffic_shaping_already_absent(self, mock_run):
        """Should handle case where tc rules absent."""
        mock_run.return_value.returncode = 1
        mgr = TrafficAnalysisManager()

        ok, msg = mgr.disable_traffic_shaping("wlan0")

        assert ok is True

    def test_add_packet_padding(self):
        """Should add random padding to payload."""
        mgr = TrafficAnalysisManager()
        original_size = 100

        padded_size = mgr.add_packet_padding(original_size)

        assert padded_size > original_size
        assert mgr.bytes_padded > 0

    def test_add_packet_padding_randomness(self):
        """Padding size should vary randomly."""
        mgr = TrafficAnalysisManager()
        sizes = []

        for _ in range(10):
            size = mgr.add_packet_padding(100)
            sizes.append(size)

        # Different padding sizes should be generated
        unique_sizes = set(sizes)
        assert len(unique_sizes) > 1

    def test_calculate_artificial_delay(self):
        """Should calculate artificial delay."""
        mgr = TrafficAnalysisManager()
        delay = mgr.calculate_artificial_delay()

        assert isinstance(delay, int)
        assert delay >= 0
        assert delay <= mgr.config.artificial_delay_ms * 2

    def test_calculate_artificial_delay_randomness(self):
        """Artificial delay should vary."""
        mgr = TrafficAnalysisManager()
        mgr.config.burst_randomization = True
        delays = [mgr.calculate_artificial_delay() for _ in range(20)]

        # Should have variation in delays
        unique_delays = set(delays)
        assert len(unique_delays) > 1

    def test_randomize_packet_sizes(self):
        """Should randomize packet size."""
        mgr = TrafficAnalysisManager()
        original_data = b"test data"

        randomized = mgr.randomize_packet_sizes(original_data)

        assert len(randomized) >= len(original_data)
        assert randomized.startswith(original_data)

    def test_randomize_packet_sizes_padding_disabled(self):
        """Should not add padding when disabled."""
        mgr = TrafficAnalysisManager()
        mgr.config.packet_padding = False
        original_data = b"test data"

        result = mgr.randomize_packet_sizes(original_data)

        assert result == original_data

    def test_randomize_packet_sizes_empty_data(self):
        """Should handle empty data."""
        mgr = TrafficAnalysisManager()
        result = mgr.randomize_packet_sizes(b"")

        assert result == b""

    def test_simulate_traffic_burst(self):
        """Should simulate traffic burst."""
        mgr = TrafficAnalysisManager()
        packets, bytes_sent = mgr.simulate_traffic_burst(100)

        assert packets > 0
        assert bytes_sent > 0
        assert mgr.packets_sent == packets

    def test_simulate_traffic_burst_zero_duration(self):
        """Should handle zero duration."""
        mgr = TrafficAnalysisManager()
        packets, bytes_sent = mgr.simulate_traffic_burst(0)

        assert packets == 0
        assert bytes_sent == 0

    def test_simulate_traffic_burst_negative_duration(self):
        """Should handle negative duration."""
        mgr = TrafficAnalysisManager()
        packets, bytes_sent = mgr.simulate_traffic_burst(-100)

        assert packets == 0
        assert bytes_sent == 0

    def test_traffic_analysis_status(self):
        """Should return traffic analysis status."""
        mgr = TrafficAnalysisManager()
        status = mgr.get_traffic_analysis_status()

        assert isinstance(status, dict)
        assert "constant_bitrate_enabled" in status
        assert "bitrate_kbps" in status
        assert "packet_padding_enabled" in status
        assert "artificial_delays_enabled" in status
        assert "burst_randomization_enabled" in status
        assert "packets_sent" in status
        assert "bytes_padded" in status
        assert "timestamp" in status

    @patch("swxtch.traffic_analysis.subprocess.run")
    def test_configure_all_analysis_prevention(self, mock_run):
        """Should enable all traffic analysis prevention."""
        mock_run.return_value.returncode = 0
        mgr = TrafficAnalysisManager()
        mgr.tc_available = True

        ok, msg = mgr.configure_all_analysis_prevention()

        assert ok is True
        assert "Traffic shaping" in msg or "bitrate" in msg.lower()
        assert "Packet padding" in msg

    def test_padding_size_ranges(self):
        """Should respect padding size ranges."""
        mgr = TrafficAnalysisManager()
        min_size, max_size = mgr.config.padding_size_range

        for _ in range(20):
            padded_size = mgr.add_packet_padding(0)
            assert padded_size >= min_size
            assert padded_size <= max_size

    def test_constant_rates_configuration(self):
        """Should have valid constant rate configurations."""
        assert "low" in CONSTANT_RATES
        assert "medium" in CONSTANT_RATES
        assert "high" in CONSTANT_RATES
        assert CONSTANT_RATES["low"] < CONSTANT_RATES["medium"] < CONSTANT_RATES["high"]

    def test_padding_sizes_configuration(self):
        """Should have valid padding size configurations."""
        assert "small" in PADDING_SIZES
        assert "medium" in PADDING_SIZES
        assert "large" in PADDING_SIZES

        for size_name, (min_size, max_size) in PADDING_SIZES.items():
            assert min_size < max_size
            assert min_size > 0

    def test_bytes_padded_tracking(self):
        """Should track total bytes padded."""
        mgr = TrafficAnalysisManager()
        initial = mgr.bytes_padded

        mgr.add_packet_padding(100)
        mgr.add_packet_padding(100)

        assert mgr.bytes_padded > initial

    def test_traffic_shaping_state_change(self):
        """Should track traffic shaping configuration."""
        mgr = TrafficAnalysisManager()
        initial_rate = mgr.config.bitrate_kbps

        mgr.config.bitrate_kbps = 512
        assert mgr.config.bitrate_kbps == 512

        mgr.config.bitrate_kbps = initial_rate
        assert mgr.config.bitrate_kbps == initial_rate
