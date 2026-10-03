"""Helpers to normalize amounts and dates found in invoices.

Invoices from different vendors use different conventions:
  - "1,234.56" (US) vs "1.234,56" (AR/EU) for amounts
  - "15/03/2026", "2026-03-15" or "Mar 15, 2026" for dates
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_AMOUNT_CHARS = re.compile(r"[^\d,.\-]")

DATE_FORMATS = (
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d.%m.%Y",
)


def parse_amount(raw: str | None) -> Decimal | None:
    """Convert an amount string into a Decimal, detecting the decimal separator.

    >>> parse_amount("$ 1,234.56")
    Decimal('1234.56')
    >>> parse_amount("ARS 1.234,56")
    Decimal('1234.56')
    """
    if raw is None:
        return None
    text = _AMOUNT_CHARS.sub("", str(raw))
    if not text or not re.search(r"\d", text):
        return None

    last_dot, last_comma = text.rfind("."), text.rfind(",")
    if last_dot != -1 and last_comma != -1:
        # The right-most separator is the decimal one.
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif last_comma != -1:
        # "1234,56" -> decimal comma; "1,234" -> thousands separator.
        decimals = len(text) - last_comma - 1
        text = text.replace(",", ".") if decimals in (1, 2) else text.replace(",", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")

    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def parse_date(raw: str | None) -> date | None:
    """Parse a date written in any of the supported invoice formats."""
    if not raw:
        return None
    value = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
