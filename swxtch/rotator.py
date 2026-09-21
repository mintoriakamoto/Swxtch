"""Background MAC-rotation logic, independent of any UI."""

import threading
import time
from dataclasses import dataclass, field

from . import netdev


@dataclass
class RotatorState:
    iface: str
    enabled: bool = True
    interval_seconds: int = 15 * 60
    original_mac: str | None = None
    current_mac: str | None = None
    last_rotated_at: float | None = None
    last_error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class Rotator:
    def __init__(self, iface: str, interval_seconds: int = 15 * 60):
        self.state = RotatorState(iface=iface, interval_seconds=interval_seconds)
        self.state.original_mac = netdev.get_mac(iface)
        self.state.current_mac = self.state.original_mac
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def rotate_now(self) -> None:
        with self.state.lock:
            new_mac = netdev.random_mac()
            ok, msg = netdev.set_mac(self.state.iface, new_mac)
            if ok:
                self.state.current_mac = new_mac
                self.state.last_rotated_at = time.time()
                self.state.last_error = None
            else:
                self.state.last_error = msg

    def restore_original(self) -> None:
        with self.state.lock:
            if self.state.original_mac:
                ok, msg = netdev.set_mac(self.state.iface, self.state.original_mac)
                if ok:
                    self.state.current_mac = self.state.original_mac
                    self.state.last_error = None
                else:
                    self.state.last_error = msg

    def toggle(self) -> bool:
        with self.state.lock:
            self.state.enabled = not self.state.enabled
            return self.state.enabled

    def set_interval(self, seconds: int) -> None:
        with self.state.lock:
            self.state.interval_seconds = max(30, seconds)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            with self.state.lock:
                enabled = self.state.enabled
                interval = self.state.interval_seconds
                last = self.state.last_rotated_at
            due = last is None or (time.time() - last) >= interval
            if enabled and due:
                self.rotate_now()
            self._stop.wait(1)
