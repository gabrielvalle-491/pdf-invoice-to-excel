"""Command line entry point.

    python -m invoice_extractor samples/ -o output/invoices.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from invoice_extractor.excel_writer import write_workbook
from invoice_extractor.extractor import extract_folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract invoice PDFs into a formatted Excel workbook")
    parser.add_argument("input_dir", type=Path, help="Folder with invoice PDFs")
    parser.add_argument("-o", "--output", type=Path, default=Path("output/invoices.xlsx"))
    args = parser.parse_args(argv)

    if not args.input_dir.is_dir():
        print(f"Input folder not found: {args.input_dir}", file=sys.stderr)
        return 1

    invoices = extract_folder(args.input_dir)
    if not invoices:
        print(f"No PDF files found in {args.input_dir}", file=sys.stderr)
        return 1

    path = write_workbook(invoices, args.output)
    review = sum(not inv.is_valid for inv in invoices)
    print(f"Processed {len(invoices)} invoices -> {path}")
    print(f"  OK: {len(invoices) - review} | Needs review: {review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
