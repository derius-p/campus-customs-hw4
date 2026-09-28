"""Database access shared by the backend modules."""

from __future__ import annotations

import os
import sqlite3
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
# CAMPUS_DB_PATH lets tests point at a copy instead of the real database.
DB_PATH = Path(os.getenv("CAMPUS_DB_PATH", DATA_DIR / "campus_customs.db"))


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


DISPLAY_DIR = DATA_DIR / "products_display"  # tidied copies made by prepare_images.py


@lru_cache(maxsize=512)
def image_info(image_file_path: str) -> tuple[str, str]:
    """(URL to show, "dark" or "light" background) for a catalog image path like "products/x.jpg".

    Uses the tidied display copy when one exists; the database path stays the source of truth.
    """
    name = Path(image_file_path).name
    if (DISPLAY_DIR / name).exists():
        url, file = f"/media/display/{name}", DISPLAY_DIR / name
    else:
        url, file = f"/media/{image_file_path}", DATA_DIR / image_file_path
    try:
        with Image.open(file) as im:
            corners = im.convert("L").resize((16, 16)).crop((0, 0, 16, 1))
            tone = "dark" if ImageStat.Stat(corners).mean[0] < 110 else "light"
    except OSError:
        tone = "light"
    return url, tone
