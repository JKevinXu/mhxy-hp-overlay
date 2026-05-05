from pathlib import Path

from PIL import Image, ImageDraw

from mhxy_hp_overlay.analyzer import analyze_hp_roi, extract_visible_hp_text


def make_hp_image(path: Path, ratio: float) -> None:
    img = Image.new("RGB", (220, 40), "black")
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 10, 210, 30), outline=(120, 120, 120), fill=(25, 25, 25))
    fill_width = int(200 * ratio)
    if fill_width > 0:
        draw.rectangle((10, 10, 10 + fill_width - 1, 30), fill=(220, 20, 20))
    img.save(path)


def test_extract_visible_hp_text():
    assert extract_visible_hp_text("气血 1234/5678") == (1234, 5678)
    assert extract_visible_hp_text("无数字") is None


def test_analyze_partial_bar(tmp_path):
    path = tmp_path / "hp.png"
    make_hp_image(path, 0.5)
    result = analyze_hp_roi(Image.open(path), (10, 10, 210, 30))
    assert result.hp_ratio is not None
    assert 0.45 <= result.hp_ratio <= 0.55
    assert result.confidence > 0.4


def test_visible_text_overrides_bar(tmp_path):
    path = tmp_path / "hp.png"
    make_hp_image(path, 0.25)
    result = analyze_hp_roi(Image.open(path), (10, 10, 210, 30), visible_text="300/1000")
    assert result.hp_ratio == 0.3
    assert result.visible_text == "300/1000"
    assert result.confidence >= 0.9
