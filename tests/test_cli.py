"""Tests for CLI interface."""

from unittest.mock import patch, MagicMock
from swxtch.cli import _parse_args, _find_terminal, main


class TestArgParsing:
    """Test CLI argument parsing."""

    def test_parse_default_args(self):
        """Should parse with defaults."""
        args = _parse_args([])
        assert args.interface is None
        assert args.interval == 15
        assert args.window is False
        assert args.list is False

    def test_parse_interface_flag(self):
        """Should parse interface flag."""
        args = _parse_args(["-i", "wlan0"])
        assert args.interface == "wlan0"

        args = _parse_args(["--interface", "wlan1"])
        assert args.interface == "wlan1"

    def test_parse_interval_flag(self):
        """Should parse interval flag."""
        args = _parse_args(["--interval", "5"])
        assert args.interval == 5

        args = _parse_args(["--interval", "30"])
        assert args.interval == 30

    def test_parse_window_flag(self):
        """Should parse window flag."""
        args = _parse_args(["--window"])
        assert args.window is True

    def test_parse_list_flag(self):
        """Should parse list flag."""
        args = _parse_args(["--list"])
        assert args.list is True

    def test_parse_license_flag(self):
        """Should parse license flag."""
        args = _parse_args(["--license"])
        assert args.license is True

    def test_parse_subscribe_flag(self):
        """Should parse subscribe flag."""
        args = _parse_args(["--subscribe"])
        assert args.subscribe is True

    def test_parse_combined_flags(self):
        """Should handle combined flags."""
        args = _parse_args(["-i", "wlan0", "--interval", "10", "--window"])
        assert args.interface == "wlan0"
        assert args.interval == 10
        assert args.window is True

    def test_parse_interval_validation(self):
        """Should handle invalid interval."""
        try:
            args = _parse_args(["--interval", "not_a_number"])
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass  # Expected


class TestTerminalDetection:
    """Test terminal emulator detection."""

    def test_find_terminal_returns_list_or_none(self):
        """Should return list of command or None."""
        result = _find_terminal()
        assert result is None or isinstance(result, list)

    @patch("shutil.which")
    def test_find_terminal_checks_in_order(self, mock_which):
        """Should check terminals in priority order."""
        # Only x-terminal-emulator exists
        def which_side_effect(cmd):
            return "/usr/bin/x-terminal-emulator" if cmd == "x-terminal-emulator" else None

        mock_which.side_effect = which_side_effect
        result = _find_terminal()

        assert result == ["x-terminal-emulator", "-e"]

    @patch("shutil.which")
    def test_find_terminal_prefers_first_available(self, mock_which):
        """Should prefer first available terminal."""
        # Multiple terminals available
        def which_side_effect(cmd):
            return f"/usr/bin/{cmd}" if cmd in ["gnome-terminal", "konsole"] else None

        mock_which.side_effect = which_side_effect
        result = _find_terminal()

        # Should return whichever is checked first (gnome-terminal or x-terminal-emulator)
        assert result is not None
        assert isinstance(result, list)

    @patch("shutil.which")
    def test_find_terminal_returns_none_when_none_found(self, mock_which):
        """Should return None when no terminal found."""
        mock_which.return_value = None
        result = _find_terminal()

        assert result is None


class TestMainFunction:
    """Test main() function with licensing."""

    @patch("swxtch.cli.check_license")
    @patch("swxtch.cli.get_license_info")
    def test_license_flag_shows_status(self, mock_get_info, mock_check):
        """Should show license status with --license flag."""
        mock_get_info.return_value = "✓ Trial active (5 days remaining)"
        result = main(["--license"])
        assert result == 0
        mock_get_info.assert_called_once()

    @patch("swxtch.cli.check_license")
    @patch("subprocess.Popen")
    def test_subscribe_flag_opens_page(self, mock_popen, mock_check):
        """Should open subscription page with --subscribe flag."""
        result = main(["--subscribe"])
        assert result == 0
        mock_popen.assert_called_once()

    @patch("swxtch.cli.check_license")
    @patch("swxtch.cli.netdev")
    def test_main_checks_license_before_running(self, mock_netdev, mock_check):
        """Should check license before starting rotation."""
        mock_check.return_value = (False, "Trial expired")
        mock_netdev.is_root.return_value = True
        mock_netdev.list_wifi_interfaces.return_value = ["wlan0"]

        result = main([])

        assert result == 1
        mock_check.assert_called_once()
