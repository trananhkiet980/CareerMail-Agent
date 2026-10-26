import os
import queue
import sys
import threading
import time

from careermail.core import config, paths
from careermail.core.observability import record_event, setup_logging
from careermail.desktop.runtime import Runtime


class SingleInstance:
    def __init__(self) -> None:
        self._fh = None
        self._path = paths.data_dir() / "careermail.lock"

    def acquire(self) -> bool:
        self._fh = open(self._path, "a+")
        try:
            if sys.platform.startswith("win"):
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            self._fh.close()
            self._fh = None
            return False

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            if sys.platform.startswith("win"):
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh, fcntl.LOCK_UN)
        except Exception:
            pass
        finally:
            self._fh.close()
            self._fh = None


class DesktopApp:
    def __init__(self) -> None:
        self.runtime = Runtime()
        self._root = None
        self._tray = None
        self._tray_available = False
        self._queue: queue.Queue = queue.Queue()
        self._quitting = False

    def post(self, func) -> None:
        self._queue.put(func)

    def _pump(self) -> None:
        try:
            while True:
                self._queue.get_nowait()()
        except queue.Empty:
            pass
        if self._root is not None and not self._quitting:
            self._root.after(100, self._pump)

    def open_settings(self) -> None:
        if self._root is not None:
            self.post(self._show_window)

    def _show_window(self) -> None:
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
        except Exception:
            pass

    def autostart_enabled(self) -> bool:
        from careermail.desktop import autostart

        return autostart.is_enabled()

    def toggle_autostart(self) -> None:
        from careermail.desktop import autostart

        autostart.set_enabled(not autostart.is_enabled())

    def quit(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        record_event("INFO", "app", "ứng dụng đang thoát")

        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
            self._tray = None

        try:
            self.runtime.stop()
        except Exception as exc:
            record_event("WARNING", "app", f"runtime.stop lỗi: {exc}")

        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:
                pass

    def on_window_close(self) -> None:
        if self._tray_available:
            try:
                self._root.withdraw()
            except Exception:
                pass
        else:
            self.quit()

    def run(self) -> None:
        from careermail.desktop.gui import SettingsWindow
        from careermail.desktop.tray import create_tray

        self.runtime.start()

        self._tray = create_tray(self)
        self._tray_available = self._tray is not None

        window = SettingsWindow(self)
        self._root = window.root
        self._root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self._pump()

        if self._tray_available:
            threading.Thread(
                target=self._tray.run, name="tray", daemon=True
            ).start()

        try:
            self._root.mainloop()
        finally:
            self.quit()


def main() -> None:
    setup_logging(config.LOG_LEVEL, config.LOG_RETENTION_DAYS)
    record_event("INFO", "app", "=== CareerMail-Agent khởi động ===")

    single = SingleInstance()
    if not single.acquire():
        record_event("WARNING", "app", "ứng dụng đã đang chạy, thoát instance này.")
        print("CareerMail-Agent đang chạy ở một tiến trình khác.")
        return

    try:
        app = DesktopApp()
        app.run()
    finally:
        single.release()
