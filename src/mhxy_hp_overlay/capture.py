from __future__ import annotations

from PIL import Image

from .models import ROI


def capture_screen_roi(roi: ROI) -> Image.Image:
    """Capture a screen ROI using mss. This is read-only pixel capture."""
    import mss

    x1, y1, x2, y2 = roi
    monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
    with mss.mss() as sct:
        shot = sct.grab(monitor)
    return Image.frombytes("RGB", shot.size, shot.rgb)
