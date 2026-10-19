# Butterfly Cursor for macOS and Linux (preview)

The same creatures as the Windows version, written with Python and Qt (PySide6).

## Run from source

```bash
python3 -m pip install pyside6-essentials
python3 cross/butterfly_cursor.py
```

The creature pictures are taken from `../src`. Settings are in the tray / menu-bar icon.

## Build a program

```bash
python3 -m pip install pyside6-essentials pyinstaller
python3 cross/build.py
```

GitHub Actions builds both systems automatically on every version tag (`.github/workflows/cross-platform.yml`).

## Notes

- **macOS:** the app is not signed. First start: right-click → *Open*, or `xattr -dr com.apple.quarantine "Butterfly Cursor.app"`.
- **Linux:** works on X11. On Wayland it starts through XWayland, because Wayland does not tell programs where the pointer is.
- Autostart: `~/Library/LaunchAgents/com.jb.butterflycursor.plist` (macOS) or `~/.config/autostart/butterfly-cursor.desktop` (Linux).
