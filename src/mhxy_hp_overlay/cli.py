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
from .damage import DamageTracker, analyze_damage_roi, extract_damage_numbers, summarize_damage_numbers
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


def print_damage_summary(summary, as_json: bool) -> None:
    if as_json:
        console.print(json.dumps(summary.to_dict(), ensure_ascii=False))
        return
    table = Table(title="MHXY visible damage summary")
    table.add_column("name")
    table.add_column("count")
    table.add_column("total_damage")
    table.add_column("max_damage")
    table.add_column("average_damage")
    table.add_column("numbers")
    table.add_row(
        summary.name,
        str(summary.count),
        str(summary.total_damage),
        "" if summary.max_damage is None else str(summary.max_damage),
        "" if summary.average_damage is None else f"{summary.average_damage:.1f}",
        ", ".join(map(str, summary.numbers)),
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


@app.command()
def analyze_damage_image(
    image_path: Annotated[Path, typer.Argument(help="Screenshot/image file to analyze")],
    roi: Annotated[str, typer.Option(help="Damage-number ROI as x1,y1,x2,y2")],
    name: Annotated[str, typer.Option(help="Display name, e.g. attack1 or target")]= "damage",
    visible_text: Annotated[
        str | None,
        typer.Option(help="Optional manual/OCR text such as '2388 666'; skips OCR if provided"),
    ] = None,
    ocr: Annotated[bool, typer.Option("--ocr", help="Run local Tesseract OCR on the ROI")]= False,
    min_amount: Annotated[int, typer.Option(help="Ignore OCR numbers smaller than this")]= 100,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON only")]= False,
) -> None:
    parsed_roi = parse_roi(roi)
    image = Image.open(image_path)
    summary = analyze_damage_roi(
        image,
        parsed_roi,
        name=name,
        visible_text=visible_text,
        use_ocr=ocr,
        min_amount=min_amount,
    )
    print_damage_summary(summary, json_output)


@app.command()
def sum_damage(
    text: Annotated[str, typer.Argument(help="Visible/OCR damage text to parse and sum")],
    name: Annotated[str, typer.Option(help="Display name")]= "damage",
    min_amount: Annotated[int, typer.Option(help="Ignore numbers smaller than this")]= 100,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON only")]= False,
) -> None:
    summary = summarize_damage_numbers(extract_damage_numbers(text, min_amount=min_amount), name=name)
    print_damage_summary(summary, json_output)


@app.command()
def watch_damage_screen(
    roi: Annotated[str, typer.Option(help="Screen ROI as x1,y1,x2,y2")],
    name: Annotated[str, typer.Option(help="Display name for this damage stream")]= "damage",
    interval: Annotated[float, typer.Option(help="Seconds between read-only captures")]= 0.5,
    dedupe_window: Annotated[
        float,
        typer.Option(help="Seconds to ignore repeated same damage number across adjacent frames"),
    ] = 0.8,
    min_amount: Annotated[int, typer.Option(help="Ignore OCR numbers smaller than this")]= 100,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON lines")]= False,
) -> None:
    parsed_roi = parse_roi(roi)
    tracker = DamageTracker(dedupe_window_seconds=dedupe_window)
    console.print("Read-only damage-number screen sampling. Press Ctrl-C to stop.")
    try:
        while True:
            image = capture_screen_roi(parsed_roi)
            summary = analyze_damage_roi(
                image,
                (0, 0, image.width, image.height),
                name=name,
                use_ocr=True,
                min_amount=min_amount,
            )
            added = tracker.add_numbers(summary.numbers, timestamp=time.time(), source=name)
            if added:
                print_damage_summary(tracker.summary(name=name), json_output)
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("Stopped.")
