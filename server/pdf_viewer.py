
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
