import argparse
import shutil
import subprocess
import sys

from . import netdev
from .tui import main_curses

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
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.list:
        ifaces = netdev.list_wifi_interfaces()
        if not ifaces:
            print("No Wi-Fi interfaces found.")
            return 1
        for name in ifaces:
            print(f"{name}\t{netdev.get_mac(name)}")
        return 0

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
