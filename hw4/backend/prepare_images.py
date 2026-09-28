"""Make tidy display copies of the product photos.

About a third of the catalog photos are a light product shot with black bars on the
left and right. This trims those bars and re-pads the photo to a square using its own
background color, so every product fills its tile evenly on the site. Originals in
data/products/ are never changed; copies go to data/products_display/ with the same
file names, and the API serves a copy when one exists.

Run from the backend folder (HW4 venv active):  python prepare_images.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageStat

DATA = Path(__file__).resolve().parent.parent / "data"
SRC, DST = DATA / "products", DATA / "products_display"
DARK = 30  # a column is "black bar" if nearly all its pixels are darker than this


def _is_bar(column: Image.Image) -> bool:
    data = column.get_flattened_data() if hasattr(column, "get_flattened_data") else column.getdata()
    pixels = list(data)
    return sum(1 for p in pixels if max(p) < DARK) / len(pixels) > 0.97


def tidy(path: Path) -> tuple[Image.Image, bool]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    left = 0
    while left < w // 3 and _is_bar(im.crop((left, 0, left + 1, h))):
        left += 1
    right = w
    while right > w * 2 // 3 and _is_bar(im.crop((right - 1, 0, right, h))):
        right -= 1
    if left < 4 and w - right < 4:
        return im, False  # no bars
    inner = im.crop((left, 0, right, h))
    # Background color: the average of the inner image's top and bottom rows.
    edge = Image.new("RGB", (inner.width, 2))
    edge.paste(inner.crop((0, 0, inner.width, 1)), (0, 0))
    edge.paste(inner.crop((0, h - 1, inner.width, h)), (0, 1))
    bg = tuple(int(v) for v in ImageStat.Stat(edge).median)
    side = max(inner.size)
    square = Image.new("RGB", (side, side), bg)
    square.paste(inner, ((side - inner.width) // 2, (side - inner.height) // 2))
    return square, True


def main() -> None:
    DST.mkdir(exist_ok=True)
    fixed = 0
    for path in sorted(SRC.glob("*.jpg")):
        image, changed = tidy(path)
        if changed:
            image.save(DST / path.name, quality=90)
            fixed += 1
        elif (DST / path.name).exists():
            (DST / path.name).unlink()
    print(f"Trimmed black bars from {fixed} photos -> {DST}")


if __name__ == "__main__":
    main()
