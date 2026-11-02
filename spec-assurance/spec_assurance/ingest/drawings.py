"""Text extraction for documents under review, including drawings.

Order of attempts per page / image:
1. PDF text layer (vector drawings, exported reports)  — exact, free.
2. Tesseract OCR, if installed (TESSERACT_CMD or on PATH) — local.
3. Claude vision transcription — needs the API; used only when 1 and 2 give nothing.
Geometry and layout are never assessed: only the words on the sheet.
"""

from __future__ import annotations

import io
import shutil
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .. import config

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".tif": "image/tiff", ".tiff": "image/tiff", ".bmp": "image/bmp"}
MIN_TEXT_CHARS = 40


@dataclass
class PageText:
    page: int
    text: str
    method: str  # pdf-text | ocr | claude-vision | none


def tesseract_available() -> bool:
    try:
        import pytesseract
    except ImportError:
        return False
    cmd = config.TESSERACT_CMD or shutil.which("tesseract")
    if not cmd:
        default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        cmd = str(default) if default.exists() else ""
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
        return True
    return False


def _ocr(png: bytes) -> str:
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(io.BytesIO(png)))


def _vision(png: bytes, media_type: str = "image/png") -> str:
    from .. import llm

    if llm.mode() != "live":
        return ""
    return llm.transcribe_image(png, media_type)


def _image_fallback(png: bytes, media_type: str = "image/png") -> tuple[str, str]:
    if tesseract_available():
        text = _ocr(png)
        if len(text.strip()) >= MIN_TEXT_CHARS:
            return text, "ocr"
    text = _vision(png, media_type)
    if text.strip():
        return text, "claude-vision"
    return "", "none"


def extract(name: str, data: bytes) -> list[PageText]:
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        doc = pymupdf.open(stream=data, filetype="pdf")
        pages = []
        for p in doc:
            text = p.get_text()
            if len(text.strip()) >= MIN_TEXT_CHARS:
                pages.append(PageText(p.number + 1, text, "pdf-text"))
                continue
            png = p.get_pixmap(dpi=200).tobytes("png")
            t, method = _image_fallback(png)
            pages.append(PageText(p.number + 1, t, method))
        return pages
    if suffix in IMAGE_TYPES:
        media = IMAGE_TYPES[suffix]
        if media not in ("image/png", "image/jpeg"):  # Claude accepts png/jpeg/gif/webp
            pix = pymupdf.Pixmap(data)
            data, media = pix.tobytes("png"), "image/png"
        t, method = _image_fallback(data, media)
        return [PageText(1, t, method)]
    if suffix == ".docx":
        from .docx_parser import parse_docx

        tmp = config.DATA_DIR / f"_upload{suffix}"
        tmp.write_bytes(data)
        try:
            parsed = parse_docx(tmp)
        finally:
            tmp.unlink(missing_ok=True)
        return [PageText(1, parsed.page_texts[0], "docx")]
    if suffix in (".txt", ".md"):
        return [PageText(1, data.decode("utf-8", errors="replace"), "text")]
    raise ValueError(f"Unsupported file type: {suffix}")
