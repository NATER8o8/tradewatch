
import os, re, hashlib
from typing import List, Dict, Any
import fitz  # PyMuPDF

STORAGE_DIR = os.environ.get("OTP_STORAGE_DIR", "data/pdfs")
os.makedirs(STORAGE_DIR, exist_ok=True)

def _ticker_candidates(text: str) -> List[str]:
    raw = set(re.findall(r"\b[A-Z]{1,5}\b", text))
    bad = {"AND","THE","FOR","FROM","WITH","THIS","THAT","NOT","YOU","YOUR","FORM","PDF","PAGE","DATE","FILE","OF","USD","EUR","SEC"}
    return [t for t in raw if t not in bad]

def extract_entities(pdf_path: str) -> Dict[str, Any]:
    doc = fitz.open(pdf_path)
    text_all = "".join([p.get_text() for p in doc])
    tickers = _ticker_candidates(text_all)
    amounts = re.findall(r"\$\s?([0-9][0-9,]*\.?[0-9]*)", text_all)
    return {"tickers": sorted(list(set(tickers)))[:100], "amounts": amounts[:100]}


def _download_to_cache(url: str) -> str:
    """Download a PDF (or return local path) into `STORAGE_DIR` and return the path.
    This is a lightweight helper used by the app; failures return empty string.
    """
    try:
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            import requests
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return ""
            h = hashlib.sha256(url.encode()).hexdigest()
            path = os.path.join(STORAGE_DIR, f"{h}.pdf")
            with open(path, "wb") as f:
                f.write(resp.content)
            return path
        # local file
        if os.path.exists(url):
            return url
    except Exception:
        return ""
    return ""


def render_page_with_highlights(pdf_path: str, page_no: int = 0, highlights: List[Dict[str, Any]] = None) -> bytes:
    """Render a single PDF page to PNG bytes with optional highlights.
    This is a minimal implementation that returns the page as PNG bytes when possible,
    or empty bytes on failure. Designed to keep imports/tests simple.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_no)
        pix = page.get_pixmap()
        return pix.tobytes("png")
    except Exception:
        return b""
