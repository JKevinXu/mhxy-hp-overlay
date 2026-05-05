from .models import ROI


def parse_roi(value: str) -> ROI:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 4:
        raise ValueError("ROI must be x1,y1,x2,y2")
    try:
        x1, y1, x2, y2 = [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError("ROI values must be integers") from exc
    if x2 <= x1 or y2 <= y1:
        raise ValueError("ROI must satisfy x2>x1 and y2>y1")
    return x1, y1, x2, y2


def crop_box_size(roi: ROI) -> tuple[int, int]:
    x1, y1, x2, y2 = roi
    return x2 - x1, y2 - y1
