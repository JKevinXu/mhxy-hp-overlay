from __future__ import annotations

import re

import cv2
import numpy as np
from PIL import Image

from .models import HPDetection, ROI

VISIBLE_HP_TEXT_RE = re.compile(r"(?P<current>\d{1,7})\s*/\s*(?P<max>\d{1,7})")


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def extract_visible_hp_text(text: str) -> tuple[int, int] | None:
    match = VISIBLE_HP_TEXT_RE.search(text)
    if not match:
        return None
    current = int(match.group("current"))
    maximum = int(match.group("max"))
    if maximum <= 0 or current < 0:
        return None
    return current, maximum


def estimate_red_hp_bar_ratio(bgr_image: np.ndarray) -> tuple[float | None, float, str | None]:
    if bgr_image.size == 0:
        return None, 0.0, "empty ROI"
    height, width = bgr_image.shape[:2]
    if width < 5 or height < 3:
        return None, 0.0, "ROI too small"

    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    lower_red_1 = np.array([0, 70, 80])
    upper_red_1 = np.array([12, 255, 255])
    lower_red_2 = np.array([170, 70, 80])
    upper_red_2 = np.array([180, 255, 255])

    mask_1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask_2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
    mask = cv2.bitwise_or(mask_1, mask_2)

    # Remove tiny noise while preserving thin UI bars.
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    red_pixels = int(np.count_nonzero(mask))
    if red_pixels == 0:
        return 0.0, 0.15, "no red HP pixels detected"

    column_red_counts = np.count_nonzero(mask, axis=0)
    # A column is considered part of the bar if at least 15% of its pixels are red.
    red_columns = column_red_counts >= max(1, int(height * 0.15))
    indices = np.flatnonzero(red_columns)
    if len(indices) == 0:
        return None, 0.2, "red pixels too sparse"

    left = int(indices[0])
    right = int(indices[-1])
    red_span = right - left + 1

    # If the crop is intended to be tight around the full bar, width is the denominator.
    ratio = max(0.0, min(1.0, red_span / width))

    density = red_pixels / float(width * height)
    continuity = len(indices) / float(red_span)
    confidence = max(0.0, min(1.0, 0.25 + density * 2.0 + continuity * 0.5))

    return ratio, confidence, None


def analyze_hp_roi(
    image: Image.Image,
    roi: ROI,
    *,
    name: str = "target",
    source: str = "image",
    visible_text: str | None = None,
) -> HPDetection:
    x1, y1, x2, y2 = roi
    crop = image.crop((x1, y1, x2, y2))
    ratio, confidence, warning = estimate_red_hp_bar_ratio(pil_to_bgr(crop))

    text_ratio = None
    parsed_text = None
    if visible_text:
        parsed = extract_visible_hp_text(visible_text)
        if parsed:
            current, maximum = parsed
            text_ratio = max(0.0, min(1.0, current / maximum))
            parsed_text = f"{current}/{maximum}"

    if text_ratio is not None:
        ratio = text_ratio
        confidence = max(confidence, 0.9)

    return HPDetection(
        name=name,
        hp_ratio=ratio,
        confidence=round(confidence, 4),
        source=source,  # type: ignore[arg-type]
        roi=roi,
        visible_text=parsed_text,
        warning=warning,
    )
