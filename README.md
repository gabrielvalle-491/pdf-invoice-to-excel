# PDF → Excel Invoice Automation

Español: [README.es.md](README.es.md)

![CI](https://github.com/gabrielvalle-491/pdf-invoice-to-excel/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Automates invoice/document extraction into structured, analyst-ready Excel files.

Drop a folder of supplier invoices (PDF) and get one Excel workbook with every
invoice, every line item, automatic totals per currency and a **Review** sheet
listing anything that does not add up — no manual typing.

## The business problem

An accounts-payable team receives dozens of supplier invoices per week, from
different vendors, in **different languages, date formats and number formats**
(`1.234,56` vs `1,234.56`, `15/03/2026` vs `Mar 15, 2026`). Someone types each one into
a spreadsheet by hand: slow, boring and error-prone.

## What this tool does

| Step | Detail |
|------|--------|
| 1. Read | Opens every PDF in a folder (text + tables) with `pdfplumber` |
| 2. Extract | Vendor, tax ID, invoice number, dates, currency, subtotal, tax, total and every line item. Works with English **and** Spanish labels |
| 3. Normalize | Detects decimal comma vs decimal point and 6 date formats automatically |
| 4. Validate | Line items = subtotal, subtotal + tax = total, qty × price = amount, due date after issue date, required fields present |
| 5. Export | Formatted Excel workbook: **Summary**, **Invoices**, **Line Items**, **Review** (with live Excel formulas, filters, frozen headers and money formats) |

Invoices that fail any check are highlighted and listed in the **Review** sheet with
the exact reason, so a human only looks at the exceptions.

## Quick start

```bash
pip install -r requirements.txt

# 1) create 8 realistic sample invoices (EN/ES, ARS/USD)
python -m invoice_extractor.generate_samples samples

# 2) extract them into Excel
python -m invoice_extractor samples -o output/invoices.xlsx
```

```
Processed 8 invoices -> output/invoices.xlsx
  OK: 8 | Needs review: 0
```

## Output

**Invoices sheet** (one row per invoice):

| File | Vendor | Invoice # | Date | Currency | Subtotal | Tax | Total | Status |
|------|--------|-----------|------|----------|---------:|----:|------:|--------|
| A-01000.pdf | Andes Office Supplies S.A. | A-01000 | 2026-03-28 | ARS | 1,016,000.00 | 213,360.00 | 1,229,360.00 | OK |
| INV-01007.pdf | BlueRiver Cloud Services LLC | INV-01007 | 2026-06-03 | USD | 109.99 | 0.00 | 109.99 | OK |

**Review sheet** (only exceptions — illustrative example):

| File | Invoice # | Issue |
|------|-----------|-------|
| broken.pdf | – | Could not read PDF |
| INV-0042.pdf | INV-0042 | Subtotal + tax does not match total |

## Project structure

```
invoice_extractor/
├── parsing.py           # amount + date normalization (multi-locale)
├── extractor.py         # PDF -> Invoice dataclass + business validation
├── excel_writer.py      # formatted workbook with formulas
├── generate_samples.py  # realistic demo invoices (reportlab)
└── cli.py               # command line interface
tests/                   # pytest suite (runs on every push via GitHub Actions)
```

## Tests

```bash
pytest -q
```

The test suite generates invoices, extracts them and checks every field against
the ground truth, plus edge cases (corrupted PDFs, wrong totals, number formats).

## Adapting it to a new vendor

Field labels live in `FIELD_PATTERNS` (`extractor.py`). Supporting a new layout is
usually one extra regex alternative, e.g. adding `Nro\. Comprobante` to the invoice
number pattern.

## How I would deliver this to a client

If you hire me for this, I would:

- Ask for a handful of real invoices from each of your vendors (PDF, with selectable text) and adjust the field labels in `FIELD_PATTERNS` until every one of them extracts cleanly.
- Set up one shared input folder: each week your team drops the new PDFs there, and nothing else changes in their routine.
- Run it with a single command (`python -m invoice_extractor <folder> -o <workbook>.xlsx`), scheduled weekly with Windows Task Scheduler or cron so the workbook is ready without anyone launching it.
- Hand over the Excel workbook as the deliverable: the **Summary** sheet shows how many invoices were processed and how many need review, with totals per currency.
- Report problems through the tool's own mechanisms: every invoice that fails a check is highlighted in **Invoices** and listed in the **Review** sheet with the exact reason (unreadable PDF, missing field, totals that do not add up, due date before issue date).
- Make the scheduled run easy to monitor: the console prints `OK: n | Needs review: n`, and a missing or empty input folder prints an error and exits with code 1, so the scheduler can flag the failed run.
- Write a short how-to for your team and add the test cases for any new vendor layout, so future changes do not break existing vendors.

## Notes

- All sample invoices are synthetic, generated by `generate_samples.py`. No real client data.
- Built with Python and [Claude Code](https://claude.com/claude-code) as an AI pair programmer.

## Author

**Gabriel Valle** — Data & AI automation (Excel, PDF, workflows) · Villa Mercedes, Argentina · Remote
