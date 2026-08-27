"""curses TUI mimicking the iOS 'Private Wi-Fi Address' panel, meant to run
as a standing terminal window."""

import curses
import time

from . import netdev
from .rotator import Rotator

HELP = "[r] rotate now   [t] toggle rotating   [+/-] interval   [q] quit"


def _fmt_since(ts: float | None) -> str:
    if ts is None:
        return "never"
    secs = int(time.time() - ts)
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    return f"{secs // 3600}h {(secs % 3600) // 60}m ago"


def _fmt_interval(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    mins = seconds // 60
    return f"{mins}m"


def run(stdscr: "curses._CursesWindow", rotator: Rotator) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)

    rotator.start()
    try:
        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            s = rotator.state

            title = " Swxtch — Private Wi-Fi Address "
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.A_BOLD)

            row = 2
            status = "Rotating" if s.enabled else "Fixed"
            color = curses.color_pair(1) if s.enabled else curses.color_pair(2)
            stdscr.addstr(row, 2, "Private Wi-Fi Address")
            stdscr.addstr(row, w - 2 - len(status), status, color | curses.A_BOLD)
            row += 2

            stdscr.addstr(row, 2, "Interface")
            stdscr.addstr(row, w - 2 - len(s.iface), s.iface)
            row += 1

            cur_mac = s.current_mac or "unknown"
            stdscr.addstr(row, 2, "Wi-Fi Address")
            stdscr.addstr(row, w - 2 - len(cur_mac), cur_mac, curses.A_BOLD)
            row += 1

            orig = s.original_mac or "unknown"
            stdscr.addstr(row, 2, "Original Address")
            stdscr.addstr(row, w - 2 - len(orig), orig, curses.A_DIM)
            row += 1

            interval = _fmt_interval(s.interval_seconds)
            stdscr.addstr(row, 2, "Rotation Interval")
            stdscr.addstr(row, w - 2 - len(interval), interval)
            row += 1

            last = _fmt_since(s.last_rotated_at)
            stdscr.addstr(row, 2, "Last Rotated")
            stdscr.addstr(row, w - 2 - len(last), last)
            row += 2

            if s.last_error:
                err = f"Error: {s.last_error}"[: w - 4]
                stdscr.addstr(row, 2, err, curses.color_pair(3))
                row += 2

            wrap = (
                "Wi-Fi networks and devices can track other nearby Wi-Fi "
                "devices by their Wi-Fi address, even on secure networks. "
                "A rotating private address reduces tracking by periodically "
                "changing this device's Wi-Fi address on this network."
            )
            for i in range(0, len(wrap), max(10, w - 4)):
                if row >= h - 2:
                    break
                stdscr.addstr(row, 2, wrap[i : i + w - 4], curses.A_DIM)
                row += 1

            if h >= 1:
                stdscr.addstr(h - 1, max(0, (w - len(HELP)) // 2), HELP[: w - 1], curses.A_DIM)

            stdscr.refresh()

            try:
                ch = stdscr.getch()
            except curses.error:
                ch = -1

            if ch in (ord("q"), ord("Q")):
                break
            elif ch in (ord("r"), ord("R")):
                rotator.rotate_now()
            elif ch in (ord("t"), ord("T")):
                rotator.toggle()
            elif ch in (ord("+"), ord("=")):
                rotator.set_interval(s.interval_seconds + 60)
            elif ch in (ord("-"), ord("_")):
                rotator.set_interval(s.interval_seconds - 60)
    finally:
        rotator.stop()


def main_curses(iface: str, interval_seconds: int) -> None:
    rotator = Rotator(iface, interval_seconds)
    curses.wrapper(run, rotator)
