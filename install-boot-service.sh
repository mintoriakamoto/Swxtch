#!/bin/bash
# Install swxtch as a systemd boot service with FIPS 206 verification

set -e

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing swxtch boot service..."

# Install crypto dependencies
echo "Installing cryptographic dependencies..."
pip install -q "cryptography>=41.0" "pycryptodome>=3.19" 2>/dev/null || true

# Try to install liboqs for MLKEM/FIPS 206 (optional, service works without it)
echo "Installing MLKEM support (FIPS 206)..."
pip install -q "liboqs-python>=0.9.0" 2>/dev/null || {
    echo "⚠️  liboqs-python installation failed (optional) - service will work with SHA3-256 only"
}

# Create boot wrapper script
echo "Creating boot wrapper..."
cat > /usr/local/bin/swxtch-boot << 'BOOTSCRIPT'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/lib/python3/dist-packages')
from swxtch.boot import boot_rotation
sys.exit(boot_rotation())
BOOTSCRIPT

chmod +x /usr/local/bin/swxtch-boot

# Copy systemd service file
echo "Installing systemd service..."
cp "$SCRIPT_DIR/swxtch-boot.service" /etc/systemd/system/swxtch-boot.service
chmod 644 /etc/systemd/system/swxtch-boot.service

# Create log directory
mkdir -p /var/log/swxtch
chmod 700 /var/log/swxtch

# Reload systemd daemon
systemctl daemon-reload

echo ""
echo "✅ Installation complete!"
echo ""
echo "To enable boot service:"
echo "  sudo systemctl enable swxtch-boot"
echo "  sudo systemctl start swxtch-boot"
echo ""
echo "To check status:"
echo "  sudo systemctl status swxtch-boot"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u swxtch-boot -f"
echo "  sudo tail -f /var/log/swxtch/changes.log"
