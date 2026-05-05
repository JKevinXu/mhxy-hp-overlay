from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated

import typer
from PIL import Image
from rich.console import Console
from rich.table import Table

from .analyzer import analyze_hp_roi
from .capture import capture_screen_roi
from .roi import parse_roi

app = typer.Typer(help="Visible-screen HP estimator for 梦幻西游手游. No automation or hidden-state access.")
console = Console()


def print_detection(result, as_json: bool) -> None:
    if as_json:
        console.print(json.dumps(result.to_dict(), ensure_ascii=False))
        return
    table = Table(title="MHXY visible HP estimate")
    table.add_column("name")
    table.add_column("hp_ratio")
    table.add_column("confidence")
    table.add_column("source")
    table.add_column("roi")
    table.add_column("warning")
    ratio = "n/a" if result.hp_ratio is None else f"{result.hp_ratio:.1%}"
    table.add_row(
        result.name,
        ratio,
        f"{result.confidence:.2f}",
        result.source,
        ",".join(map(str, result.roi)),
        result.warning or "",
    )
    console.print(table)


@app.command()
def analyze_image(
    image_path: Annotated[Path, typer.Argument(help="Screenshot/image file to analyze")],
    roi: Annotated[str, typer.Option(help="ROI as x1,y1,x2,y2")],
    name: Annotated[str, typer.Option(help="Display name for this HP bar")] = "target",
    visible_text: Annotated[str | None, typer.Option(help="Optional visible text such as 1234/5678")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON only")] = False,
) -> None:
    parsed_roi = parse_roi(roi)
    image = Image.open(image_path)
    result = analyze_hp_roi(image, parsed_roi, name=name, source="image", visible_text=visible_text)
    print_detection(result, json_output)


@app.command()
def watch_screen(
    roi: Annotated[str, typer.Option(help="Screen ROI as x1,y1,x2,y2")],
    name: Annotated[str, typer.Option(help="Display name for this HP bar")] = "target",
    interval: Annotated[float, typer.Option(help="Seconds between read-only captures")] = 0.5,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON lines")] = False,
) -> None:
    parsed_roi = parse_roi(roi)
    console.print("Read-only screen sampling. Press Ctrl-C to stop.")
    try:
        while True:
            image = capture_screen_roi(parsed_roi)
            result = analyze_hp_roi(image, (0, 0, image.width, image.height), name=name, source="screen")
            # Report original screen ROI, not cropped local ROI.
            result = type(result)(
                name=result.name,
                hp_ratio=result.hp_ratio,
                confidence=result.confidence,
                source=result.source,
                roi=parsed_roi,
                method=result.method,
                visible_text=result.visible_text,
                warning=result.warning,
            )
            print_detection(result, json_output)
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("Stopped.")
