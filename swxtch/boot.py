"""Boot-time MAC and IP rotation with FIPS 206 verification."""

import subprocess
import sys
import time
from pathlib import Path

from . import netdev
from .crypto import verify_mac_change, verify_ip_change, log_verification


def get_current_ip(iface: str) -> str | None:
    """Get current IP address for interface."""
    try:
        result = subprocess.run(
            ["ip", "addr", "show", iface],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.split("\n"):
            if "inet " in line:
                return line.strip().split()[1].split("/")[0]
    except Exception:
        pass
    return None


def renew_dhcp(iface: str) -> bool:
    """Request new DHCP lease to get new IP."""
    try:
        # Try dhclient first
        subprocess.run(
            ["dhclient", "-r", iface],
            capture_output=True,
            timeout=5,
        )
        time.sleep(1)
        subprocess.run(
            ["dhclient", iface],
            capture_output=True,
            timeout=10,
        )
        return True
    except Exception:
        try:
            # Fallback to systemd-networkd
            subprocess.run(
                ["systemctl", "restart", f"systemd-networkd"],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception:
            return False


def boot_rotation(iface: str | None = None) -> int:
    """
    Run MAC rotation on boot, change IP, and verify with FIPS 206 crypto.
    This is meant to be called by systemd service at startup.
    """
    print("[swxtch-boot] Starting MAC and IP rotation at boot...")

    # Check root
    if not netdev.is_root():
        print("[swxtch-boot] ERROR: Must run as root", file=sys.stderr)
        return 1

    # Find interface
    if not iface:
        interfaces = netdev.list_wifi_interfaces()
        if not interfaces:
            print("[swxtch-boot] ERROR: No Wi-Fi interfaces found", file=sys.stderr)
            return 1
        iface = interfaces[0]

    print(f"[swxtch-boot] Using interface: {iface}")

    # Get current state
    old_mac = netdev.get_mac(iface)
    old_ip = get_current_ip(iface)

    print(f"[swxtch-boot] Current MAC: {old_mac}")
    print(f"[swxtch-boot] Current IP: {old_ip}")

    # Rotate MAC
    print("[swxtch-boot] Rotating MAC address...")
    new_mac = netdev.random_mac()
    ok, msg = netdev.set_mac(iface, new_mac)

    if not ok:
        print(f"[swxtch-boot] ERROR setting MAC: {msg}", file=sys.stderr)
        return 1

    print(f"[swxtch-boot] MAC changed to: {new_mac}")

    # Verify MAC change
    mac_record = verify_mac_change(old_mac, new_mac, iface)
    print(f"[swxtch-boot] MAC verification (SHA3-256): {mac_record['new_mac_hash_sha3_256'][:16]}...")

    if "mlkem_encrypted" in mac_record:
        print("[swxtch-boot] MAC change encrypted with MLKEM (FIPS 206)")

    # Renew DHCP for new IP
    print("[swxtch-boot] Requesting new DHCP lease...")
    time.sleep(1)  # Wait for interface to stabilize

    if renew_dhcp(iface):
        time.sleep(2)  # Wait for IP to be assigned
        new_ip = get_current_ip(iface)

        if new_ip and new_ip != old_ip:
            print(f"[swxtch-boot] IP changed to: {new_ip}")
            ip_record = verify_ip_change(old_ip, new_ip, iface)
            print(f"[swxtch-boot] IP verification (SHA3-256): {ip_record['new_ip_hash_sha3_256'][:16]}...")

            if "mlkem_encrypted" in ip_record:
                print("[swxtch-boot] IP change encrypted with MLKEM (FIPS 206)")
        else:
            print(f"[swxtch-boot] WARNING: IP did not change (still {new_ip})")
            new_ip = new_ip or old_ip
            ip_record = verify_ip_change(old_ip, new_ip, iface)
    else:
        print("[swxtch-boot] WARNING: DHCP renewal failed")
        new_ip = get_current_ip(iface) or old_ip
        ip_record = verify_ip_change(old_ip, new_ip, iface)

    # Log both changes
    try:
        log_verification(mac_record, ip_record)
        print("[swxtch-boot] Verification logged to /var/log/swxtch/changes.log")
    except Exception as e:
        print(f"[swxtch-boot] WARNING: Could not write log: {e}", file=sys.stderr)

    print("[swxtch-boot] Boot rotation complete ✓")
    return 0


if __name__ == "__main__":
    iface = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(boot_rotation(iface))
