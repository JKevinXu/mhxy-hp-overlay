from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean

from PIL import Image

from .models import ROI

DAMAGE_TOKEN_RE = re.compile(r"(?<![\d/])(?P<sign>[+-]?)(?P<amount>\d{2,7})(?![\d/])")
RATIO_RE = re.compile(r"\d{1,7}\s*/\s*\d{1,7}")


@dataclass(frozen=True)
class DamageEvent:
    amount: int
    timestamp: float
    source: str = "visible"

    def to_dict(self) -> dict:
        return {"amount": self.amount, "timestamp": self.timestamp, "source": self.source}


@dataclass(frozen=True)
class DamageSummary:
    name: str
    count: int
    total_damage: int
    max_damage: int | None
    average_damage: float | None
    numbers: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "total_damage": self.total_damage,
            "max_damage": self.max_damage,
            "average_damage": self.average_damage,
            "numbers": self.numbers,
        }


def _remove_hp_ratios(text: str) -> str:
    return RATIO_RE.sub(" ", text)


def extract_damage_numbers(text: str, *, min_amount: int = 10) -> list[int]:
    """Extract visible damage/healing numbers from OCR/manual text.

    Positive unsigned numbers are treated as visible damage candidates.
    A leading '-' is also treated as damage. A leading '+' is healing and is
    included. HP ratios such as 1234/5678 are ignored.
    """
    cleaned = _remove_hp_ratios(text)
    numbers: list[int] = []
    for match in DAMAGE_TOKEN_RE.finditer(cleaned):
        amount = int(match.group("amount"))
        if amount < min_amount:
            continue
        numbers.append(amount)
    return numbers


def summarize_damage_numbers(numbers: list[int], *, name: str = "damage") -> DamageSummary:
    return DamageSummary(
        name=name,
        count=len(numbers),
        total_damage=sum(numbers),
        max_damage=max(numbers) if numbers else None,
        average_damage=float(mean(numbers)) if numbers else None,
        numbers=list(numbers),
    )


def ocr_visible_damage_text(image: Image.Image) -> str:
    """OCR visible damage digits from a cropped screenshot.

    Requires the optional pytesseract Python package and the tesseract binary.
    The OCR config is intentionally restricted to digits and +/- signs because
    the first MVP only needs visible damage numbers.
    """
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("pytesseract is not installed; install package extras or pass --visible-text") from exc

    config = "--psm 6 -c tessedit_char_whitelist=0123456789+-/"
    return pytesseract.image_to_string(image, config=config)


def analyze_damage_roi(
    image: Image.Image,
    roi: ROI,
    *,
    name: str = "damage",
    visible_text: str | None = None,
    use_ocr: bool = False,
    min_amount: int = 10,
) -> DamageSummary:
    x1, y1, x2, y2 = roi
    crop = image.crop((x1, y1, x2, y2))
    text = visible_text if visible_text is not None else ""
    if use_ocr and not text:
        text = ocr_visible_damage_text(crop)
    return summarize_damage_numbers(extract_damage_numbers(text, min_amount=min_amount), name=name)


class DamageTracker:
    """Rolling visible damage tracker with simple short-window de-duplication."""

    def __init__(self, *, dedupe_window_seconds: float = 0.8) -> None:
        self.dedupe_window_seconds = dedupe_window_seconds
        self.events: list[DamageEvent] = []
        self._recent_seen: dict[int, float] = {}

    def add_numbers(
        self,
        numbers: list[int],
        *,
        timestamp: float,
        source: str = "visible",
    ) -> list[DamageEvent]:
        added: list[DamageEvent] = []
        for amount in numbers:
            last_seen = self._recent_seen.get(amount)
            if last_seen is not None and timestamp - last_seen < self.dedupe_window_seconds:
                continue
            event = DamageEvent(amount=amount, timestamp=timestamp, source=source)
            self.events.append(event)
            self._recent_seen[amount] = timestamp
            added.append(event)
        return added

    def summary(self, *, name: str = "damage") -> DamageSummary:
        return summarize_damage_numbers([event.amount for event in self.events], name=name)
