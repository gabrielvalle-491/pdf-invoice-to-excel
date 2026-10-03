"""Generate realistic sample invoices (PDF) to demo and test the extractor.

Vendors use different languages, date formats and number formats on purpose,
because that is what real accounts-payable inboxes look like.

Usage:
    python -m invoice_extractor.generate_samples samples/
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass
class VendorStyle:
    """Layout and locale conventions used by one fictional vendor."""

    name: str
    tax_id: str
    lang: str  # "en" or "es"
    date_fmt: str
    decimal_comma: bool
    currency: str
    tax_rate: Decimal


VENDORS = [
    VendorStyle("Andes Office Supplies S.A.", "30-71234567-9", "es", "%d/%m/%Y", True, "ARS", Decimal("0.21")),
    VendorStyle("BlueRiver Cloud Services LLC", "84-1234567", "en", "%Y-%m-%d", False, "USD", Decimal("0.00")),
    VendorStyle("Distribuidora Cuyo SRL", "30-70987654-2", "es", "%d-%m-%Y", True, "ARS", Decimal("0.21")),
    VendorStyle("Northwind Logistics Inc.", "47-9876543", "en", "%b %d, %Y", False, "USD", Decimal("0.07")),
]

PRODUCTS = {
    "es": [
        ("Resma papel A4 75g", Decimal("8500")),
        ("Toner impresora laser", Decimal("62000")),
        ("Silla ergonomica", Decimal("185000")),
        ("Servicio de mantenimiento mensual", Decimal("95000")),
        ("Flete y entrega", Decimal("24000")),
        ("Cajas de archivo x10", Decimal("15500")),
    ],
    "en": [
        ("Cloud hosting - monthly plan", Decimal("249.00")),
        ("Support hours", Decimal("45.00")),
        ("Freight - pallet", Decimal("180.00")),
        ("Storage fee (per week)", Decimal("35.50")),
        ("Software license - seat", Decimal("19.99")),
        ("Onboarding session", Decimal("150.00")),
    ],
}

LABELS = {
    "es": {
        "title": "FACTURA", "number": "Factura N°", "date": "Fecha", "due": "Vencimiento",
        "bill_to": "Cliente", "tax_id": "CUIT", "desc": "Descripción", "qty": "Cant.",
        "unit": "Precio unit.", "amount": "Importe", "subtotal": "Subtotal", "tax": "IVA", "total": "TOTAL",
    },
    "en": {
        "title": "INVOICE", "number": "Invoice No", "date": "Invoice Date", "due": "Due Date",
        "bill_to": "Bill To", "tax_id": "Tax ID", "desc": "Description", "qty": "Qty",
        "unit": "Unit Price", "amount": "Amount", "subtotal": "Subtotal", "tax": "Tax", "total": "TOTAL",
    },
}


def fmt_amount(value: Decimal, decimal_comma: bool) -> str:
    """Format an amount with US (1,234.56) or AR/EU (1.234,56) separators."""
    text = f"{value:,.2f}"
    if decimal_comma:
        text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return text


def build_invoice(path: Path, vendor: VendorStyle, number: str, issued: date, rng: random.Random) -> dict:
    """Render one invoice PDF at `path` and return its ground-truth values."""
    labels = LABELS[vendor.lang]
    items = []
    for desc, price in rng.sample(PRODUCTS[vendor.lang], k=rng.randint(2, 5)):
        qty = rng.randint(1, 12)
        items.append((desc, qty, price, price * qty))

    subtotal = sum(i[3] for i in items)
    tax = (subtotal * vendor.tax_rate).quantize(Decimal("0.01"))
    total = subtotal + tax

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=f"{labels['title']} {number}")
    story = [
        Paragraph(f"<b>{vendor.name}</b>", styles["Title"]),
        Paragraph(f"{labels['tax_id']}: {vendor.tax_id}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>{labels['title']}</b>", styles["Heading2"]),
        Paragraph(f"{labels['number']}: {number}", styles["Normal"]),
        Paragraph(f"{labels['date']}: {issued.strftime(vendor.date_fmt)}", styles["Normal"]),
        Paragraph(f"{labels['due']}: {(issued + timedelta(days=30)).strftime(vendor.date_fmt)}", styles["Normal"]),
        Paragraph(f"{labels['bill_to']}: Demo Client Co.", styles["Normal"]),
        Spacer(1, 12),
    ]

    rows = [[labels["desc"], labels["qty"], labels["unit"], labels["amount"]]]
    for desc, qty, price, amount in items:
        rows.append([desc, str(qty), fmt_amount(price, vendor.decimal_comma), fmt_amount(amount, vendor.decimal_comma)])
    table = Table(rows, colWidths=[250, 50, 90, 90])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    story += [
        table,
        Spacer(1, 12),
        Paragraph(f"{labels['subtotal']}: {vendor.currency} {fmt_amount(subtotal, vendor.decimal_comma)}", styles["Normal"]),
        Paragraph(f"{labels['tax']}: {vendor.currency} {fmt_amount(tax, vendor.decimal_comma)}", styles["Normal"]),
        Paragraph(f"<b>{labels['total']}: {vendor.currency} {fmt_amount(total, vendor.decimal_comma)}</b>", styles["Normal"]),
    ]
    doc.build(story)
    return {"number": number, "vendor": vendor.name, "date": issued, "subtotal": subtotal, "tax": tax, "total": total,
            "items": len(items)}


def generate(out_dir: Path, count: int = 8, seed: int = 7) -> list[dict]:
    """Create `count` invoices in `out_dir` and return the ground truth for each one."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    truth = []
    start = date(2026, 1, 5)
    for i in range(count):
        vendor = VENDORS[i % len(VENDORS)]
        number = f"{'A' if vendor.lang == 'es' else 'INV'}-{1000 + i * 7:05d}"
        issued = start + timedelta(days=rng.randint(0, 240))
        path = out_dir / f"{number}.pdf"
        truth.append({"file": path.name, **build_invoice(path, vendor, number, issued, rng)})
    return truth


def main() -> None:
    """Command line entry point for generating sample invoices."""
    parser = argparse.ArgumentParser(prog="python -m invoice_extractor.generate_samples",
                                     description="Generate sample invoice PDFs")
    parser.add_argument("out_dir", type=Path, nargs="?", default=Path("samples"))
    parser.add_argument("--count", type=int, default=8)
    args = parser.parse_args()
    truth = generate(args.out_dir, args.count)
    print(f"Generated {len(truth)} invoices in {args.out_dir}")


if __name__ == "__main__":
    main()
