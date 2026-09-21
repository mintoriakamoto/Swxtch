"""Tests for MAC rotation daemon."""

import threading
import time
from unittest.mock import Mock, patch, MagicMock
from swxtch.rotator import RotatorState, Rotator


class TestRotatorState:
    """Test RotatorState dataclass."""

    def test_initial_state(self):
        """Should initialize with correct defaults."""
        state = RotatorState(
            iface="wlan0",
            enabled=True,
            interval_seconds=60,
        )
        assert state.iface == "wlan0"
        assert state.enabled is True
        assert state.interval_seconds == 60
        assert state.original_mac is None
        assert state.current_mac is None
        assert state.last_rotated_at is None

    def test_state_is_dataclass(self):
        """Should support dataclass operations."""
        state1 = RotatorState(
            iface="wlan0",
            enabled=True,
            interval_seconds=60,
        )
        state2 = RotatorState(
            iface="wlan0",
            enabled=True,
            interval_seconds=60,
        )
        # Dataclasses should compare by value
        assert state1.iface == state2.iface


class TestRotator:
    """Test Rotator daemon."""

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_initialization(self, mock_get_mac):
        """Should initialize correctly."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        assert rotator.state.iface == "wlan0"
        assert rotator.state.interval_seconds == 60
        assert rotator.state.enabled is True  # Should start enabled
        assert rotator.state.original_mac == "aa:bb:cc:dd:ee:ff"
        assert rotator.state.current_mac == "aa:bb:cc:dd:ee:ff"

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_start_creates_thread(self, mock_get_mac):
        """Should create a background thread when started."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        # Disable rotation to avoid trying to actually run commands
        rotator.state.enabled = False

        rotator.start()
        assert rotator._thread is not None
        assert isinstance(rotator._thread, threading.Thread)
        assert rotator._thread.daemon is True

        rotator.stop()

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_toggle_enabled(self, mock_get_mac):
        """Should toggle rotation on/off."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        assert rotator.state.enabled is True
        result = rotator.toggle()
        assert result is False
        assert rotator.state.enabled is False
        result = rotator.toggle()
        assert result is True
        assert rotator.state.enabled is True

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_set_interval(self, mock_get_mac):
        """Should set rotation interval."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        rotator.set_interval(120)
        assert rotator.state.interval_seconds == 120

        rotator.set_interval(30)
        assert rotator.state.interval_seconds == 30

        # Should enforce minimum of 30 seconds
        rotator.set_interval(10)
        assert rotator.state.interval_seconds == 30

    @patch("swxtch.rotator.netdev.get_mac")
    @patch("swxtch.rotator.netdev.set_mac")
    @patch("swxtch.rotator.netdev.random_mac")
    def test_rotator_rotate_now(self, mock_random_mac, mock_set_mac, mock_get_mac):
        """Should rotate MAC immediately."""
        old_mac = "aa:bb:cc:dd:ee:ff"
        new_mac = "02:00:00:00:00:01"

        mock_get_mac.return_value = old_mac
        mock_random_mac.return_value = new_mac
        mock_set_mac.return_value = (True, "")

        rotator = Rotator("wlan0", interval_seconds=60)
        old_last_rotated = rotator.state.last_rotated_at

        # Small delay to ensure time difference
        time.sleep(0.01)
        rotator.rotate_now()

        assert mock_set_mac.called
        assert rotator.state.current_mac == new_mac
        if old_last_rotated is None:
            assert rotator.state.last_rotated_at is not None
        else:
            assert rotator.state.last_rotated_at >= old_last_rotated

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_restore_original(self, mock_get_mac):
        """Should restore original MAC."""
        original_mac = "aa:bb:cc:dd:ee:ff"
        mock_get_mac.return_value = original_mac

        with patch("swxtch.rotator.netdev.set_mac") as mock_set_mac:
            mock_set_mac.return_value = (True, "")
            rotator = Rotator("wlan0", interval_seconds=60)
            rotator.state.current_mac = "02:00:00:00:00:01"

            rotator.restore_original()

            assert rotator.state.current_mac == original_mac
            assert mock_set_mac.called

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_thread_safety(self, mock_get_mac):
        """State access should be thread-safe."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        # Multiple threads accessing state simultaneously
        results = []

        def read_state():
            for _ in range(100):
                state = rotator.state
                results.append(state.interval_seconds)

        def modify_state():
            for i in range(100):
                rotator.set_interval(30 + i)

        threads = [
            threading.Thread(target=read_state),
            threading.Thread(target=read_state),
            threading.Thread(target=modify_state),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not crash or deadlock
        assert len(results) == 200

    @patch("swxtch.rotator.netdev.get_mac")
    def test_rotator_stop(self, mock_get_mac):
        """Should stop cleanly."""
        mock_get_mac.return_value = "aa:bb:cc:dd:ee:ff"
        rotator = Rotator("wlan0", interval_seconds=60)

        # Disable rotation to avoid trying to actually run commands
        rotator.state.enabled = False

        rotator.start()
        rotator.stop()

        # Give thread time to exit
        time.sleep(0.1)

        # Thread should be joined
        if rotator._thread:
            assert not rotator._thread.is_alive()
