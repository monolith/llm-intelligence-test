"""Turning raw export strings into dates and amounts.

The reader for each system decides which date layout and which units apply to
its own columns; these helpers only do the conversion, and raise
:class:`~ledgerkit.core.records.LedgerParseError` with a readable message when a
field cannot be read.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError

_LAYOUT_NAMES: dict[str, str] = {"%Y": "YYYY", "%m": "MM", "%d": "DD"}


def _layout(date_format: str) -> str:
    """Spell a ``strptime`` format the way an operator would, e.g. ``DD/MM/YYYY``."""
    text = date_format
    for directive, name in _LAYOUT_NAMES.items():
        text = text.replace(directive, name)
    return text


def parse_date(raw: str, date_format: str, what: str) -> date:
    """Read ``raw`` as a date written in ``date_format``.

    ``what`` names the field in error messages, for example ``"Calder txn_date"``.
    """
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(
            f"{what} {raw!r} is not a date in the form {_layout(date_format)}"
        ) from exc


def parse_dollars(raw: str, what: str) -> Decimal:
    """Read ``raw`` as a decimal number of dollars."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"{what} {raw!r} is not a number") from exc
    if not text or not value.is_finite():
        raise LedgerParseError(f"{what} {raw!r} is not a number")
    return value
