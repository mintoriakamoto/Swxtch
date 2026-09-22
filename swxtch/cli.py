import argparse
import shutil
import subprocess
import sys

from . import netdev
from . import privacy
from . import sync
from .tui import main_curses
from .license import check_license, get_license_info, get_subscription_status, activate_license_key

TERMINALS = [
    ["x-terminal-emulator", "-e"],
    ["gnome-terminal", "--"],
    ["konsole", "-e"],
    ["xfce4-terminal", "-e"],
    ["alacritty", "-e"],
    ["kitty"],
    ["xterm", "-e"],
]


def _find_terminal() -> list[str] | None:
    for cmd in TERMINALS:
        if shutil.which(cmd[0]):
            return cmd
    return None


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="swxtch",
        description="Rotate your Wi-Fi MAC address on Linux, like iOS's Private Wi-Fi Address.",
    )
    p.add_argument("-i", "--interface", help="Wi-Fi interface to rotate (auto-detected if omitted)")
    p.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Rotation interval in minutes (default: 15)",
    )
    p.add_argument(
        "--window",
        action="store_true",
        help="Relaunch swxtch inside a new terminal window and exit this shell",
    )
    p.add_argument("--list", action="store_true", help="List detected Wi-Fi interfaces and exit")
    p.add_argument("--license", action="store_true", help="Show license and trial status")
    p.add_argument("--subscribe", action="store_true", help="Open subscription page")
    p.add_argument("--activate", metavar="KEY", help="Activate a license key (sk_live_* format)")
    p.add_argument("--privacy", action="store_true", help="Enable advanced privacy hardening (DHCP, DNS, VPN checks)")
    p.add_argument("--privacy-status", action="store_true", help="Show privacy hardening status")
    p.add_argument("--verify-privacy", action="store_true", help="Run comprehensive privacy verification")

    # Multi-device sync
    p.add_argument("--pair-device", metavar="NAME:HOST", help="Pair a second PC (format: DeviceName:192.168.1.100)")
    p.add_argument("--sync-status", action="store_true", help="Show multi-device sync status")
    p.add_argument("--paired-devices", action="store_true", help="List all paired devices")
    p.add_argument("--unpair-device", metavar="DEVICE_ID", help="Unpair a device")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.license:
        print(get_license_info())
        return 0

    if args.subscribe:
        print("Opening subscription page...")
        subprocess.Popen(["xdg-open", "https://swxtch.io/pricing"])
        return 0

    if args.activate:
        success, message = activate_license_key(args.activate)
        print(message)
        return 0 if success else 1

    if args.privacy:
        if not netdev.is_root():
            print("Privacy hardening requires root privileges (try: sudo swxtch --privacy).", file=sys.stderr)
            return 1

        iface = args.interface
        if not iface:
            candidates = netdev.list_wifi_interfaces()
            if not candidates:
                print("No Wi-Fi interfaces found.", file=sys.stderr)
                return 1
            iface = candidates[0]

        print("🔐 Enabling advanced privacy hardening...\n")

        ok1, msg1 = privacy.configure_dhcp_privacy(iface)
        print(msg1)

        ok2, msg2 = privacy.configure_dns_privacy("cloudflare")
        print(msg2)

        ok3, msg3 = privacy.prevent_ipv6_leaks(iface)
        print(msg3)

        ok4, msg4 = privacy.prevent_ipv4_leaks()
        if not ok4:
            print(msg4)
        else:
            print(msg4)

        ok5, msg5 = privacy.block_webrtc_leaks()
        print(msg5)

        return 0 if all([ok1, ok2, ok3]) else 1

    if args.privacy_status:
        status = privacy.get_privacy_status()
        print("\n🔐 Privacy Hardening Status\n")
        print(f"Overall Privacy Score: {status['overall_privacy_score']}/100")
        print(f"  • DHCP Privacy: {'✓' if status['dhcp_privacy'] else '✗'}")
        print(f"  • DNS Privacy: {'✓' if status['dns_privacy'] else '✗'}")
        print(f"  • IPv4 Protected: {'✓' if status['ipv4_protected'] else '✗'}")
        print(f"  • IPv6 Protected: {'✓' if status['ipv6_protected'] else '✗'}")
        return 0

    if args.verify_privacy:
        all_good, report = privacy.verify_privacy_hardening()
        print("\n🔐 Privacy Verification Report\n")
        print(report)
        print(f"\n{'✓ All privacy checks passed!' if all_good else '⚠️  Some privacy checks failed - review above'}\n")
        return 0 if all_good else 1

    # Multi-device sync commands
    if args.pair_device:
        sync_mgr = sync.get_sync_manager()
        try:
            name, host = args.pair_device.split(":")
            success, message = sync_mgr.pair_device(name.strip(), host.strip())
            print(message)
            return 0 if success else 1
        except ValueError:
            print("Format: --pair-device DeviceName:192.168.1.100", file=sys.stderr)
            return 1

    if args.sync_status:
        sync_mgr = sync.get_sync_manager()
        status = sync_mgr.get_sync_status()
        print("\n🔄 Multi-Device Sync Status\n")
        print(f"Device ID: {status['device_id']}")
        print(f"Paired Devices: {status['paired_devices']}")
        print(f"Online Devices: {status['online_devices']}")
        print(f"Sync Enabled: {'✓' if status['sync_enabled'] else '✗'}")
        return 0

    if args.paired_devices:
        sync_mgr = sync.get_sync_manager()
        devices = sync_mgr.get_paired_devices()
        if not devices:
            print("No paired devices")
            return 0

        print("\n🔗 Paired Devices\n")
        for device in devices:
            status = "🟢" if device["is_online"] else "🔴"
            print(f"{status} {device['name']} ({device['device_id'][:8]}...)")
            print(f"   Host: {device['host']}:{device['port']}")
            print(f"   Role: {device['role']}")
            print(f"   Paired: {device['paired_at']}")
        return 0

    if args.unpair_device:
        sync_mgr = sync.get_sync_manager()
        if args.unpair_device in sync_mgr.devices:
            device = sync_mgr.devices[args.unpair_device]
            del sync_mgr.devices[args.unpair_device]
            sync_mgr._save_devices()
            print(f"✓ Device '{device.name}' unpaired")
            return 0
        else:
            print(f"✗ Device not found: {args.unpair_device}", file=sys.stderr)
            return 1

    if args.list:
        ifaces = netdev.list_wifi_interfaces()
        if not ifaces:
            print("No Wi-Fi interfaces found.")
            return 1
        for name in ifaces:
            print(f"{name}\t{netdev.get_mac(name)}")
        return 0

    # Check license before running
    allowed, message = check_license()
    if not allowed:
        print(message, file=sys.stderr)
        return 1

    iface = args.interface
    if not iface:
        candidates = netdev.list_wifi_interfaces()
        if not candidates:
            print("No Wi-Fi interfaces found. Pass one with -i/--interface.", file=sys.stderr)
            return 1
        iface = candidates[0]

    if not netdev.is_root():
        print("swxtch needs root privileges to change MAC addresses (try: sudo swxtch).", file=sys.stderr)
        return 1

    if args.window:
        term = _find_terminal()
        if not term:
            print("No terminal emulator found; running in this window instead.", file=sys.stderr)
        else:
            cmd = term + [
                "python3",
                "-m",
                "swxtch",
                "-i",
                iface,
                "--interval",
                str(args.interval),
            ]
            subprocess.Popen(cmd)
            return 0

    main_curses(iface, args.interval * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
