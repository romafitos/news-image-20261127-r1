# news-image-20261127 entry: hands in the front page for Friday 27 November 2026.
# The page itself is drawn by draw.py (Pillow, run on our machine); the grader has
# only the Python standard library, so this program just copies the finished image.
import os


BOT = os.environ.get("MAKEFUN_BOT_DIR", os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

src = os.path.join(BOT, "entry.png")
os.makedirs(OUT, exist_ok=True)
with open(src, "rb") as f:
    data = f.read()
with open(os.path.join(OUT, "entry.png"), "wb") as f:
    f.write(data)
print(f"wrote entry.png ({len(data)} bytes)")
