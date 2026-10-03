import subprocess
import sys
from datetime import date
from decimal import Decimal

import pytest

from invoice_extractor.cli import main
from invoice_extractor.extractor import Invoice, LineItem, _parse_items, validate
from invoice_extractor.parsing import parse_date


def test_help_exits_zero_with_module_prog_name():
    result = subprocess.run([sys.executable, "-m", "invoice_extractor", "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.startswith("usage: python -m invoice_extractor")


def test_cli_returns_error_for_missing_or_empty_folder(tmp_path, capsys):
    assert main([str(tmp_path / "does-not-exist")]) == 1
    assert "Input folder not found" in capsys.readouterr().err
    assert main([str(tmp_path), "-o", str(tmp_path / "out.xlsx")]) == 1
    assert "No PDF files found" in capsys.readouterr().err
    assert not (tmp_path / "out.xlsx").exists()


@pytest.mark.parametrize("raw", [None, "", "   ", "31/02/2026", "2026/03/15", "next Friday"])
def test_parse_date_rejects_invalid_or_unsupported(raw):
    assert parse_date(raw) is None


def test_validate_reports_missing_fields_no_items_and_due_date_before_issue():
    inv = Invoice(source_file="x.pdf", date=date(2026, 3, 15), due_date=date(2026, 3, 1))
    issues = validate(inv)
    assert "Missing field: number" in issues
    assert "Missing field: total" in issues
    assert "No line items found" in issues
    assert "Due date is before invoice date" in issues


def test_parse_items_skips_unrelated_tables_and_blank_rows():
    tables = [
        [["Bill To", "Address"], ["Demo Client Co.", "Somewhere"]],
        [["Descripción", "Cant.", "Precio unit.", "Importe"],
         ["Flete y entrega", "2", "24.000,00", "48.000,00"],
         [None, None, None, None],
         ["", "1", "1,00", "1,00"]],
    ]
    assert _parse_items(tables) == [
        LineItem("Flete y entrega", Decimal("2.00"), Decimal("24000.00"), Decimal("48000.00")),
    ]
