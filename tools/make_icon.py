"""Generate ``assets/icon.ico`` and ``assets/icon.png``.

The artwork is not stored as a binary; it is the same code that draws the icons
in the interface, rendered into files. Regenerate after any change to
:mod:`app.ui.icons`:

    python tools/make_icon.py

Qt can write single-image ICO files, but Windows renders a multi-size icon much
better in Explorer and the taskbar, so the container is assembled here.
"""

from __future__ import annotations

import argparse
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QBuffer, QIODevice, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage  # noqa: E402

from app.ui.icons import app_icon_pixmap  # noqa: E402

#: Sizes Windows asks for, from the taskbar up to the extra-large shell icon.
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

#: The artwork is drawn larger and then scaled down, which antialiases the
#: tile edges far better than drawing a 16x16 badge directly.
_SUPERSAMPLE = 4

ICO_DIRECTORY = struct.Struct("<HHH")
ICO_ENTRY = struct.Struct("<BBBBHHII")


def png_bytes(size: int, accent: str) -> bytes:
    """Render the application badge as a ``size`` x ``size`` PNG.

    The image carries no device-pixel-ratio, so an ICO entry's dimensions
    always match the bytes behind it.
    """
    large = app_icon_pixmap(
        size * _SUPERSAMPLE, accent, device_pixel_ratio=1.0
    ).toImage()
    image: QImage = large.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    ).convertToFormat(QImage.Format.Format_ARGB32)
    image.setDevicePixelRatio(1.0)

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Qt could not encode the icon as PNG")
    return bytes(buffer.data())


def build_ico(payloads: list, sizes: list) -> bytes:
    """Assemble a multi-size .ico container from PNG payloads."""
    count = len(payloads)
    offset = ICO_DIRECTORY.size + ICO_ENTRY.size * count

    directory = ICO_DIRECTORY.pack(0, 1, count)
    entries = bytearray()
    for size, payload in zip(sizes, payloads):
        # 0 means 256 in the ICO format.
        dimension = 0 if size >= 256 else size
        entries += ICO_ENTRY.pack(
            dimension, dimension, 0, 0, 1, 32, len(payload), offset
        )
        offset += len(payload)

    return directory + bytes(entries) + b"".join(payloads)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accent", default="#4c8dff",
                        help="badge colour (default: the dark theme accent)")
    parser.add_argument("--output", default=str(ROOT / "assets"),
                        help="directory to write into")
    args = parser.parse_args(argv)

    # A GUI application is only needed to create pixmaps; it never shows a window.
    app = QGuiApplication.instance() or QGuiApplication([])

    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    payloads = [png_bytes(size, args.accent) for size in ICON_SIZES]

    ico_path = output / "icon.ico"
    ico_path.write_bytes(build_ico(payloads, list(ICON_SIZES)))
    print(f"Wrote {ico_path} ({ico_path.stat().st_size:,} bytes, "
          f"{len(ICON_SIZES)} sizes)")

    png_path = output / "icon.png"
    png_path.write_bytes(payloads[-1])
    print(f"Wrote {png_path} ({png_path.stat().st_size:,} bytes, 256x256)")

    del app
    return 0


if __name__ == "__main__":
    sys.exit(main())
