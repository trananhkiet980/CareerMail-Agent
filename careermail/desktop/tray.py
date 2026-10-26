from PIL import Image

from careermail.core import paths


def create_tray(app):
    try:
        import pystray
    except ImportError:
        return None

    icon_path = paths.resource_path("assets", "icon.png")
    if not icon_path.is_file():
        icon_path = paths.resource_path("assets", "icon.ico")
    if not icon_path.is_file():
        image = Image.new("RGBA", (64, 64), color=(37, 99, 235, 255))
    else:
        image = Image.open(icon_path)

    menu = pystray.Menu(
        pystray.MenuItem("Cài đặt / Settings", lambda _icon, _item: app.open_settings(), default=True),
        pystray.MenuItem(
            "Khởi động cùng máy",
            lambda _icon, _item: app.toggle_autostart(),
            checked=lambda _item: app.autostart_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Thoát / Exit", lambda _icon, _item: app.quit()),
    )
    return pystray.Icon("CareerMail-Agent", image, "CareerMail-Agent", menu)
