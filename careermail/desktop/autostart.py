import os
import sys
from pathlib import Path

from careermail.core import paths

_TASK_NAME = paths.APP_NAME


def is_enabled() -> bool:
    if sys.platform.startswith("win"):
        return _win_is_enabled()
    if sys.platform == "darwin":
        return _mac_is_enabled()
    return _linux_is_enabled()


def set_enabled(enabled: bool) -> bool:
    if sys.platform.startswith("win"):
        return _win_set_enabled(enabled)
    if sys.platform == "darwin":
        return _mac_set_enabled(enabled)
    return _linux_set_enabled(enabled)


def _executable_command() -> str:
    if paths.is_frozen():
        return f'"{sys.executable}"'
    python = sys.executable
    return f'"{python}" -m careermail'


# --- Windows Registry ---
def _win_is_enabled() -> bool:
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, _TASK_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def _win_set_enabled(enabled: bool) -> bool:
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            if enabled:
                winreg.SetValueEx(
                    key, _TASK_NAME, 0, winreg.REG_SZ, _executable_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, _TASK_NAME)
                except FileNotFoundError:
                    pass
            return True
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


# --- macOS / Linux Fallbacks ---
def _mac_plist() -> Path:
    return Path.home() / f"Library/LaunchAgents/com.careermail.{_TASK_NAME.lower()}.plist"


def _mac_is_enabled() -> bool:
    return _mac_plist().is_file()


def _mac_set_enabled(enabled: bool) -> bool:
    plist = _mac_plist()
    if not enabled:
        try:
            plist.unlink(missing_ok=True)
            return True
        except Exception:
            return False
    plist.parent.mkdir(parents=True, exist_ok=True)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.careermail.{_TASK_NAME.lower()}</string>
  <key>ProgramArguments</key><array><string>{sys.executable}</string><string>-m</string><string>careermail</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>"""
    try:
        plist.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def _linux_desktop_file() -> Path:
    return Path.home() / f".config/autostart/{_TASK_NAME.lower()}.desktop"


def _linux_is_enabled() -> bool:
    return _linux_desktop_file().is_file()


def _linux_set_enabled(enabled: bool) -> bool:
    f = _linux_desktop_file()
    if not enabled:
        try:
            f.unlink(missing_ok=True)
            return True
        except Exception:
            return False
    f.parent.mkdir(parents=True, exist_ok=True)
    content = f"""[Desktop Entry]
Type=Application
Name={_TASK_NAME}
Exec={_executable_command()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    try:
        f.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False
