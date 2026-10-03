"""Core extraction logic: one PDF in, one structured `Invoice` out."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

import pdfplumber

from invoice_extractor.parsing import parse_amount, parse_date

# Each field accepts English and Spanish labels.
FIELD_PATTERNS = {
    "number": r"(?:Invoice\s*No|Invoice\s*#|Factura\s*N[°ºo]?)\s*[:#]?\s*([A-Z0-9\-]+)",
    "date": r"(?:Invoice\s*Date|Fecha(?!\s*de\s*venc))\s*:\s*(.+)",
    "due_date": r"(?:Due\s*Date|Vencimiento)\s*:\s*(.+)",
    "tax_id": r"(?:Tax\s*ID|CUIT)\s*:\s*([\d\-]+)",
    "subtotal": r"^Subtotal\s*:\s*(.+)$",
    "tax": r"^(?:Tax|IVA)\s*:\s*(.+)$",
    "total": r"^TOTAL\s*:\s*(.+)$",
    "currency": r"^TOTAL\s*:\s*([A-Z]{3})",
}

ITEM_HEADERS = {
    "description": ("description", "descripción", "descripcion"),
    "quantity": ("qty", "cant.", "cantidad"),
    "unit_price": ("unit price", "precio unit."),
    "amount": ("amount", "importe"),
}


@dataclass
class LineItem:
    description: str
    quantity: Decimal | None
    unit_price: Decimal | None
    amount: Decimal | None


@dataclass
class Invoice:
    source_file: str
    vendor: str | None = None
    tax_id: str | None = None
    number: str | None = None
    date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    items: list[LineItem] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _parse_items(tables: list[list[list[str | None]]]) -> list[LineItem]:
    """Find the line-items table by its header row and convert each data row."""
    for table in tables:
        if not table:
            continue
        header = [(cell or "").strip().lower() for cell in table[0]]
        columns = {}
        for key, names in ITEM_HEADERS.items():
            for idx, cell in enumerate(header):
                if cell in names:
                    columns[key] = idx
        if len(columns) < len(ITEM_HEADERS):
            continue
        items = []
        for row in table[1:]:
            if not row or not row[columns["description"]]:
                continue
            items.append(LineItem(
                description=row[columns["description"]].strip(),
                quantity=parse_amount(row[columns["quantity"]]),
                unit_price=parse_amount(row[columns["unit_price"]]),
                amount=parse_amount(row[columns["amount"]]),
            ))
        return items
    return []


def validate(invoice: Invoice) -> list[str]:
    """Business checks an accounts-payable analyst would do by hand."""
    issues = []
    for name in ("number", "date", "total"):
        if getattr(invoice, name) is None:
            issues.append(f"Missing field: {name}")
    if not invoice.items:
        issues.append("No line items found")

    tolerance = Decimal("0.02")
    if invoice.items and invoice.subtotal is not None:
        items_sum = sum((i.amount or Decimal(0)) for i in invoice.items)
        if abs(items_sum - invoice.subtotal) > tolerance:
            issues.append(f"Line items ({items_sum}) do not add up to subtotal ({invoice.subtotal})")
    for item in invoice.items:
        if None not in (item.quantity, item.unit_price, item.amount):
            if abs(item.quantity * item.unit_price - item.amount) > tolerance:
                issues.append(f"Wrong line amount: {item.description}")
    if None not in (invoice.subtotal, invoice.tax, invoice.total):
        if abs(invoice.subtotal + invoice.tax - invoice.total) > tolerance:
            issues.append("Subtotal + tax does not match total")
    if invoice.date and invoice.due_date and invoice.due_date < invoice.date:
        issues.append("Due date is before invoice date")
    return issues


def extract_invoice(pdf_path: str | Path) -> Invoice:
    """Extract all fields and line items from a single invoice PDF."""
    pdf_path = Path(pdf_path)
    invoice = Invoice(source_file=pdf_path.name)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            tables = [t for page in pdf.pages for t in page.extract_tables()]
    except Exception as exc:  # corrupted or encrypted PDFs go to the review sheet
        invoice.issues.append(f"Could not read PDF: {exc}")
        return invoice

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    invoice.vendor = lines[0] if lines else None
    invoice.number = _search(FIELD_PATTERNS["number"], text)
    invoice.tax_id = _search(FIELD_PATTERNS["tax_id"], text)
    invoice.date = parse_date(_search(FIELD_PATTERNS["date"], text))
    invoice.due_date = parse_date(_search(FIELD_PATTERNS["due_date"], text))
    invoice.currency = _search(FIELD_PATTERNS["currency"], text)
    invoice.subtotal = parse_amount(_search(FIELD_PATTERNS["subtotal"], text))
    invoice.tax = parse_amount(_search(FIELD_PATTERNS["tax"], text))
    invoice.total = parse_amount(_search(FIELD_PATTERNS["total"], text))
    invoice.items = _parse_items(tables)
    invoice.issues = validate(invoice)
    return invoice


def extract_folder(folder: str | Path) -> list[Invoice]:
    """Process every PDF in a folder (sorted for reproducible output)."""
    return [extract_invoice(p) for p in sorted(Path(folder).glob("*.pdf"))]
