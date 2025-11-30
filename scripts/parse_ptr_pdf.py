#!/usr/bin/env python3
"""Extract transactions from a House PTR PDF into JSON/CSV."""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image
from pytesseract import Output

COLUMN_MAP = {
    "transactiondate": "transaction_date",
    "transaction date": "transaction_date",
    "transactiondate (mm/dd/yyyy)": "transaction_date",
    "transactiondate(mm/dd/yyyy)": "transaction_date",
    "notificationdate": "reported_date",
    "notification date": "reported_date",
    "datereported": "reported_date",
    "owner": "owner",
    "ticker": "ticker",
    "ticker(s)": "ticker",
    "assettype": "asset_type",
    "asset type": "asset_type",
    "assetname": "asset_name",
    "asset": "asset_name",
    "type": "transaction_type",
    "transactiontype": "transaction_type",
    "transaction type": "transaction_type",
    "comment": "comment",
    "comments": "comment",
    "amountof transaction": "amount",
    "amount": "amount",
    "amount oftransaction": "amount",
}

HEADER_KEYWORDS = ("transaction", "owner", "amount")


def normalize(cell: str | None) -> str:
    if not cell:
        return ""
    return " ".join(cell.strip().lower().split())


def detect_header_row(table):
    for idx, row in enumerate(table):
        combined = " ".join(normalize(cell) for cell in row if cell)
        if combined and all(word in combined for word in HEADER_KEYWORDS):
            return idx, row
    return None, None


def extract_tables(pdf_path: Path):
    entries = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables or []:
                header_idx, header_row = detect_header_row(table)
                if header_idx is None:
                    continue
                mapping = []
                for cell in header_row:
                    key = normalize(cell)
                    mapping.append(COLUMN_MAP.get(key))
                for row in table[header_idx + 1 :]:
                    if not any((cell or "").strip() for cell in row):
                        continue
                    record = {"source_page": page_index, "confidence": 1.0}
                    for idx, cell in enumerate(row):
                        if idx >= len(mapping):
                            continue
                        col = mapping[idx]
                        if not col:
                            continue
                        text = (cell or "").strip()
                        if not text:
                            continue
                        if col in record:
                            record[col] = f"{record[col]} {text}".strip()
                        else:
                            record[col] = text
                    if len(record) > 1:
                        entries.append(record)
    return entries


def ocr_page(page):
    """Return rows of text extracted via OCR along with confidence."""
    pil_img: Image.Image = page.to_image(resolution=300).original
    data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)
    rows: list[tuple[str, float]] = []
    current_tokens = []
    current_conf = []
    last_top = None
    for idx, raw_text in enumerate(data["text"]):
        text = raw_text.strip()
        if not text:
            continue
        top = data["top"][idx]
        conf_val = data["conf"][idx]
        try:
            conf = float(conf_val)
        except ValueError:
            conf = 0.0
        if last_top is None or abs(top - last_top) <= 8:
            current_tokens.append(text)
            current_conf.append(conf)
        else:
            if current_tokens:
                rows.append((" ".join(current_tokens), statistics.mean(current_conf)))
            current_tokens = [text]
            current_conf = [conf]
        last_top = top
    if current_tokens:
        rows.append((" ".join(current_tokens), statistics.mean(current_conf)))
    return rows


def extract_with_ocr(pdf_path: Path):
    fallback_entries = []
    confidences = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            rows = ocr_page(page)
            for text, conf in rows:
                lower = text.lower()
                if any(keyword in lower for keyword in HEADER_KEYWORDS):
                    continue
                fallback_entries.append(
                    {"source_page": page_index, "ocr_text": text, "confidence": conf / 100.0}
                )
                confidences.append(conf / 100.0)
    avg_conf = statistics.mean(confidences) if confidences else 0.0
    return fallback_entries, avg_conf


def write_output(entries, output, fmt):
    if fmt == "json":
        json.dump(entries, output, indent=2)
    else:
        fieldnames = sorted({k for entry in entries for k in entry.keys()})
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)


def main():
    parser = argparse.ArgumentParser(description="Extract House PTR transactions from a PDF")
    parser.add_argument("pdf", type=Path, help="Path to PTR PDF")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", "-o", type=Path, help="Output file (defaults to stdout)")
    args = parser.parse_args()

    entries = extract_tables(args.pdf)
    avg_conf = None
    if not entries:
        entries, avg_conf = extract_with_ocr(args.pdf)
        if entries:
            print(f"OCR fallback confidence ≈ {avg_conf:.2f}", file=sys.stderr)
        else:
            print("No tables detected (PDF may need manual review)", file=sys.stderr)
    else:
        print("Extracted structured tables (confidence = 1.0)", file=sys.stderr)

    if args.output:
        with args.output.open("w", encoding="utf-8", newline="" if args.format == "csv" else None) as fh:
            write_output(entries, fh, args.format)
    else:
        write_output(entries, sys.stdout, args.format)


if __name__ == "__main__":
    main()
