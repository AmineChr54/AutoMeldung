from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os
from typing import Optional

def image_to_pdf_a4(image_path: str, out_pdf_path: str) -> str:
    """Convert an image to an A4-sized single-page PDF, centered and scaled to fit."""
    c = canvas.Canvas(out_pdf_path, pagesize=A4)
    img = ImageReader(image_path)
    iw, ih = img.getSize()
    pw, ph = A4
    scale = min(pw / iw, ph / ih)
    w, h = iw * scale, ih * scale
    x, y = (pw - w) / 2, (ph - h) / 2
    c.drawImage(img, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
    c.showPage()
    c.save()
    return out_pdf_path

def _find_au_file_by_prefix(dir_path: str, prefix: str) -> Optional[str]:
    """Find a file in dir_path whose name starts with prefix (case-insensitive).
    Prefer PDFs over images; if multiple, pick the most recent by mtime.
    Returns absolute path or None.
    """
    if not os.path.isdir(dir_path):
        return None
    prefix_lower = prefix.lower()
    matches = []
    for fname in os.listdir(dir_path):
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath):
            continue
        if fname.lower().startswith(prefix_lower):
            matches.append(fpath)
    if not matches:
        return None
    def rank(path: str):
        ext = os.path.splitext(path)[1].lower()
        is_pdf = 0 if ext == ".pdf" else 1  # prefer pdf (0 < 1)
        mtime = os.path.getmtime(path)
        return (is_pdf, -mtime)  # prefer pdf, then newest
    matches.sort(key=rank)
    return matches[0]