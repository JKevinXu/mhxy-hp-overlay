from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "synthetic_hp_bar.png"
out.parent.mkdir(parents=True, exist_ok=True)
img = Image.new("RGB", (220, 40), "black")
draw = ImageDraw.Draw(img)
draw.rectangle((10, 10, 210, 30), outline=(120, 120, 120), fill=(25, 25, 25))
draw.rectangle((10, 10, 149, 30), fill=(220, 20, 20))
img.save(out)
print(out)
