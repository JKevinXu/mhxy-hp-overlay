from dataclasses import asdict, dataclass
from typing import Literal

ROI = tuple[int, int, int, int]


@dataclass(frozen=True)
class HPDetection:
    name: str
    hp_ratio: float | None
    confidence: float
    source: Literal["image", "screen"]
    roi: ROI
    method: str = "visible_red_bar_hsv"
    visible_text: str | None = None
    warning: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["roi"] = list(self.roi)
        return data
