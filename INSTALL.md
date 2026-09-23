# Installation Guide — Swxtch

Complete setup instructions for boot-verified Wi-Fi privacy on Linux.

## Pricing & Trial

**Swxtch is FREE for 7 days.** No credit card required to start your trial.

- **Free Trial:** 7 days full access (starts on first installation)
- **Premium:** $9.99/month after trial ends
- **Cancel anytime:** No long-term commitment required

Check your trial status at any time:
```bash
swxtch --license
```

After your trial expires, upgrade to continue using Swxtch:
```bash
swxtch --subscribe
```

## System Requirements

| Component | Requirement | Why |
|-----------|-------------|-----|
| OS | Linux kernel 4.4+ | MAC address changes require kernel support |
| Python | 3.10+ | Type hints, modern async |
| Disk | 50 MB | Application + crypto libraries |
| RAM | 256 MB | Systemd service + TUI |
| CPU | Any | SHA3-256 and MLKEM are fast |
| Network | DHCP-capable Wi-Fi | For IP renewal on boot |

## Step 1: Install System Dependencies

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    iproute2 \
    isc-dhcp-client \
    gnome-terminal
```

### Fedora / RHEL

```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    iproute \
    dhcp-client \
    gnome-terminal
```

### Arch / Manjaro

```bash
sudo pacman -S \
    python \
    python-pip \
    iproute2 \
    dhcp \
    gnome-terminal
```

## Step 2: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Swxtch.git
cd Swxtch
```

## Step 3: Install Swxtch with Crypto Support

### Option A: System-wide (Recommended)

```bash
pip install -e ".[crypto]"
```

This installs:
- `cryptography>=41.0` — SHA3-256 and crypto utilities
- `pycryptodome>=3.19` — Additional crypto functions
- `liboqs-python>=0.9.0` — MLKEM (optional, post-quantum)

### Option B: Virtual Environment (Isolated)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[crypto]"
```

Use this if you want isolation from system Python.

### Verify Installation

```bash
python3 -c "from swxtch import cli; print('✓ Swxtch installed')"
swxtch --help
```

## Step 4: Set Up Boot Service

### Install Service

```bash
sudo bash ./install-boot-service.sh
```

This:
- Creates `/usr/local/bin/swxtch-boot` wrapper
- Copies systemd service to `/etc/systemd/system/swxtch-boot.service`
- Creates log directory `/var/log/swxtch` (mode 700, root-only)
- Reloads systemd daemon

### Enable for Next Boot

```bash
sudo systemctl enable swxtch-boot
```

### Test Immediately (Optional)

```bash
sudo systemctl start swxtch-boot
sudo journalctl -u swxtch-boot -f
```

## Step 5: Verify Setup

### Check Service Status

```bash
sudo systemctl status swxtch-boot
```

Expected output:
```
● swxtch-boot.service - Swxtch - Boot-time MAC and IP rotation...
   Loaded: loaded (/etc/systemd/system/swxtch-boot.service; enabled)
   Active: inactive (dead) since ... (will run at next boot)
```

### Check Log Directory

```bash
ls -la /var/log/swxtch/
```

Expected:
```
drwx------ 2 root root 4096 ... /var/log/swxtch
-rw------- 1 root root   ... ... /var/log/swxtch/changes.log
```

### Run Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v
```

Expected: **31/31 tests passing** ✓

## Step 6: Reboot and Verify

```bash
sudo reboot
```

**On boot:**
1. Systemd runs swxtch-boot service
2. MAC address rotates
3. IP lease renews
4. Changes are verified and logged
5. Boot continues with new verified identities

**After boot:**

```bash
# Check boot logs
sudo journalctl -u swxtch-boot

# View verification log
sudo cat /var/log/swxtch/changes.log | python3 -m json.tool
```

Expected log entry:
```json
{
  "timestamp": "2026-09-21T08:30:45.123456",
  "mac_verification": {
    "change_verified": true,
    "new_mac_hash_sha3_256": "[HASH_MASKED]..."
  },
  "ip_verification": {
    "change_verified": true,
    "new_ip_hash_sha3_256": "[HASH_MASKED]..."
  }
}
```

## Optional: Interactive TUI Setup

For real-time control (in addition to boot service):

```bash
# Test with 1-minute rotation
sudo swxtch --interval 1

# Open in new terminal window
sudo swxtch --window

# Run in background with specific interface
nohup sudo swxtch -i wlan0 --interval 15 &
```

## Troubleshooting Installation

### "Python 3.10 not found"

```bash
# Check installed version
python3 --version

# Install from source if needed
sudo apt install python3.10-dev
```

### "pip: command not found"

```bash
# Install pip
sudo apt install python3-pip

# Or upgrade pip
python3 -m pip install --upgrade pip
```

### "liboqs installation failed"

This is OK—MLKEM is optional. Service works perfectly with SHA3-256:

```bash
# Verify it's optional
python3 -c "import oqs" 2>/dev/null && echo "✓ MLKEM available" || echo "✗ SHA3-256 only"
```

To install MLKEM anyway:

```bash
# Ubuntu/Debian
sudo apt install liboqs-dev liboqs0
pip install liboqs-python

# Fedora
sudo dnf install liboqs-devel
pip install liboqs-python

# Or from source
git clone https://github.com/open-quantum-safe/liboqs-python.git
cd liboqs-python
pip install -e .
```

### "Permission denied" on boot service

```bash
# Verify sudo access
sudo whoami  # Should output: root

# Reinstall service
sudo bash ./install-boot-service.sh
```

### Service doesn't start on boot

```bash
# Check if enabled
sudo systemctl is-enabled swxtch-boot  # Should output: enabled

# Enable if disabled
sudo systemctl enable swxtch-boot

# Check for errors
sudo journalctl -u swxtch-boot -e
```

## Uninstallation

### Remove Boot Service

```bash
sudo systemctl disable swxtch-boot
sudo systemctl stop swxtch-boot
sudo rm /etc/systemd/system/swxtch-boot.service
sudo rm /usr/local/bin/swxtch-boot
sudo systemctl daemon-reload
```

### Restore Original MAC (Optional)

```bash
# Get current MAC
ip link show wlan0 | grep link/ether

# Restore original (if you saved it)
sudo ip link set dev wlan0 address AA:BB:CC:DD:EE:FF
```

### Uninstall Python Package

```bash
pip uninstall swxtch
```

### Keep or Remove Logs

```bash
# View logs before deleting
sudo cat /var/log/swxtch/changes.log

# Remove log directory
sudo rm -rf /var/log/swxtch
```

## Advanced Configuration

### Custom Interface

Edit `/etc/systemd/system/swxtch-boot.service`:

```ini
[Service]
ExecStart=/usr/local/bin/swxtch-boot wlan0  # Specify interface
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart swxtch-boot
```

### Disable Boot Service, Keep TUI

```bash
sudo systemctl disable swxtch-boot
sudo systemctl stop swxtch-boot

# TUI still works manually
sudo swxtch --interval 15 --window
```

### Run Both (Boot + TUI)

```bash
# Boot service: automatic rotation on startup
sudo systemctl enable swxtch-boot

# TUI: manual control during session
sudo swxtch --interval 15 &
```

### View All Configuration

```bash
# Systemd service
sudo cat /etc/systemd/system/swxtch-boot.service

# Boot script
cat /usr/local/bin/swxtch-boot

# Application code
cat swxtch/boot.py
cat swxtch/crypto.py
```

## Verification Checklist

- [ ] Python 3.10+ installed
- [ ] `pip install -e ".[crypto]"` succeeded
- [ ] `swxtch --help` works
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Boot service installed: `sudo systemctl status swxtch-boot`
- [ ] Service enabled: `sudo systemctl is-enabled swxtch-boot` → enabled
- [ ] System rebooted
- [ ] Boot logs show MAC rotation: `sudo journalctl -u swxtch-boot`
- [ ] Verification log exists: `sudo cat /var/log/swxtch/changes.log`

## Support

If installation fails:

1. **Check OS**: `uname -a` (should be Linux)
2. **Check Python**: `python3 --version` (should be 3.10+)
3. **Check permissions**: `sudo whoami` (should be root)
4. **Check systemd**: `systemctl --version`
5. **View logs**: `sudo journalctl -u swxtch-boot -n 50`

Then create an issue with:
- OS version
- Python version
- Error message from `install-boot-service.sh`
- Output of `sudo journalctl -u swxtch-boot -e`

---

**Installation complete!** Your system is now set for boot-verified privacy. 🔒
