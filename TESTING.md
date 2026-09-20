# Testing & Verification Guide for Swxtch

This document outlines how to verify that swxtch correctly implements MAC address rotation on Linux.

## Quick Verification (No Hardware Required)

### 1. Unit Tests
Run the automated test suite to verify the core logic:

```bash
pip install pytest
pytest tests/ -v
```

This validates:
- MAC address generation produces valid locally-administered addresses
- MAC parsing correctly extracts addresses from system output
- Interface detection logic works correctly
- State management handles concurrent access safely

### 2. CLI Functionality
Test the command-line interface:

```bash
# List detected Wi-Fi interfaces (no root required)
swxtch --list

# Check help text
swxtch --help
```

## Testing on Real Hardware

### Prerequisites
- A Linux system with a Wi-Fi adapter
- Root privileges
- Optional: `ip` command (iproute2 - present on virtually all distros)
- Optional: `nmcli` (from NetworkManager) if using Network Manager

### 1. Manual MAC Rotation Test

**Before running:**
```bash
# Note your current MAC address
sudo ip link show wlan0 | grep link/ether

# Note any connected networks
nmcli device show wlan0 | grep -i ssid
# or
iw wlan0 link
```

**Run swxtch:**
```bash
# Start swxtch (will use first detected Wi-Fi interface)
sudo swxtch --interval 1

# Inside the TUI, press:
# - 'r' to rotate immediately
# - Watch the "Current MAC" field change
# - Watch "Last rotated" timestamp update
# - Observe Wi-Fi reconnects briefly
```

**Verify the change:**
```bash
# In another terminal, check the MAC address changed:
sudo ip link show wlan0 | grep link/ether

# Should show a different address, with locally-administered bit set
# (2nd hex digit will be odd: x2, x6, xA, xE)
```

### 2. NetworkManager Coordination Test
If using NetworkManager (check with `nmcli -t -f NAME,AUTOCONNECT conn`):

```bash
# Swxtch will automatically coordinate with NM
# Watch for:
# - No connection drops when rotating
# - Wi-Fi reconnects to the same SSID
# - No manual reconnection needed

sudo swxtch --interval 2

# Rotate a few times by pressing 'r' repeatedly
# Monitor connection status in another terminal:
nmcli device status
```

### 3. Toggle Test
Verify the on/off toggle works:

```bash
sudo swxtch --interval 5

# Press 't' to toggle rotation off
# Wait 30 seconds - no rotation should occur
# Verify status shows "Rotating: Off" or similar
# Press 't' again to re-enable
# Verify rotation resumes
```

### 4. Interval Adjustment Test
Verify dynamic interval changes:

```bash
sudo swxtch --interval 10

# Press '+' to increase interval (should go to 11 minutes)
# Press '-' to decrease interval (should go back to 10 minutes)
# Verify the "Interval" field updates
# Verify rotation timing changes accordingly
```

### 5. Persistence Test
Verify the address persists after quitting:

```bash
# Note the current MAC address shown in TUI
sudo swxtch --interval 1

# Let it rotate a few times
# Press 'q' to quit
# Immediately check the MAC address in another terminal:
sudo ip link show wlan0 | grep link/ether

# Should show the last rotated MAC (not the original)
# Swxtch leaves the interface with the final random address
```

## Automated Test Suite

### Running All Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest tests/ -v --cov=swxtch --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Files
- `tests/test_netdev.py` - Network device primitives (MAC generation, parsing, interface detection)
- `tests/test_rotator.py` - Rotation daemon logic (state management, threading, interval handling)
- `tests/test_cli.py` - CLI argument parsing and mode selection

## Expected Behavior Checklist

### MAC Address Generation
- [x] Generates 48-bit MAC addresses in correct format
- [x] Sets locally-administered bit (bit 1 of first octet = 1)
- [x] Clears multicast bit (bit 0 of first octet = 0)
- [x] All bits after the first octet are randomized
- [x] Each generated address is unique (no collisions in repeated generation)

### Interface Detection
- [x] Auto-detects wireless interfaces from `/sys/class/net/*/wireless`
- [x] Correctly lists multiple Wi-Fi adapters if present
- [x] Handles systems with no wireless interfaces gracefully
- [x] Works with different interface naming schemes (wlan0, wlp3s0, etc.)

### MAC Application
- [x] Applies address via `ip link set dev <iface> address <mac>`
- [x] Brings interface down/up correctly
- [x] Works with NetworkManager-managed devices (via nmcli coordination)
- [x] Handles permission errors when not root
- [x] Handles device errors gracefully

### TUI Display
- [x] Shows current MAC address
- [x] Shows original MAC address
- [x] Shows rotation interval
- [x] Shows time since last rotation
- [x] Shows enabled/disabled status
- [x] Updates in real-time
- [x] Responds to keybindings (r, t, +, -, q)
- [x] Exits cleanly on 'q'

### Rotation Daemon
- [x] Rotates on the specified interval
- [x] Can be toggled on/off without exiting
- [x] Can be interrupted for manual rotation
- [x] Safely handles state mutations
- [x] Thread-safe access to shared state

## Troubleshooting

### "No Wi-Fi interfaces found"
- Verify your adapter exists: `ls /sys/class/net/*/wireless`
- Check interface naming: `ip link show`
- Some drivers might not expose wireless capability via sysfs

### Wi-Fi doesn't reconnect after rotation
- Ensure NetworkManager is running (if it was managing the connection)
- Check dmesg for driver errors: `dmesg | tail -20`
- Some chipsets don't support MAC address changes on the fly
- Try using a different interface if available

### MAC address reverts after rotation
- Check if NetworkManager is resetting it: `nmcli -t conn show <SSID>`
- Some network managers force the original MAC on reconnect
- Swxtch should coordinate automatically; check for errors in stderr

### Permission denied errors
- Ensure you're running with sudo: `sudo swxtch`
- Check you have CAP_NET_ADMIN: `sudo getcap /usr/bin/ip`

## Platform Notes

### Ubuntu/Debian
- Works out of the box with NetworkManager or systemd-networkd
- Terminal emulators supported: gnome-terminal, xterm, alacritty, kitty

### Fedora/RHEL
- Works with NetworkManager by default
- Terminal emulators supported: konsole, xterm

### Arch/Manjaro
- Works with both NetworkManager and iwd
- Most terminal emulators supported

## Continuous Integration

Consider adding CI tests for:
- Linting (flake8, pylint)
- Type checking (mypy)
- Format checking (black)
- Unit test suite (pytest)

Example GitHub Actions workflow would run these checks on each push.
