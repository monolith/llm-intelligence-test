"""Check export files for malformed rows."""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit.config import load_settings, Settings
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system

_log = get_logger(__name__)


def validate(files: list[str]) -> int:
    """Validate export files without writing anything.

    Args:
        files: List of export file paths.

    Returns:
        Exit code (0 if all valid, 2 if any rejected).
    """
    settings = load_settings()
    total_checked = 0
    total_rejected = 0

    for file_path in files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except Exception as exc:
            _log.warning("cannot read %s: %s", path.name, exc)
            total_rejected += 1
            continue

        checked, rejected = validate_file(path, system, settings)
        total_checked += checked
        total_rejected += rejected

    from ledgerkit.cli import emit
    emit(f"checked={total_checked} rejected={total_rejected}")

    return 2 if total_rejected > 0 else 0


def validate_file(path: Path, system: str, settings: Settings) -> tuple[int, int]:
    """Validate one export file."""
    from ledgerkit.core import fields

    checked = 0
    rejected = 0
    pattern = re.compile(settings.account_code_pattern)

    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    if system == "A":
        data_lines = [
            (i + 1, line.rstrip("\r\n"))
            for i, line in enumerate(lines)
            if not line.startswith("#") and line.strip()
        ]
        if not data_lines:
            return 0, 1
        header_line = data_lines[0][1]
        header = fields.split_record(header_line)
        data_lines = data_lines[1:]
    elif system == "B":
        data_lines = [(i + 1, line.rstrip("\r\n")) for i, line in enumerate(lines) if line.strip()]
        if not data_lines:
            return 0, 1
        header_line = data_lines[0][1]
        header = header_line.split(",")
        data_lines = data_lines[1:]
    else:
        data_lines = [(i + 1, line.rstrip("\r\n")) for i, line in enumerate(lines) if line.strip()]
        if len(data_lines) < 3:
            return 0, 1
        header_line = data_lines[1][1]
        header = header_line.split(",")
        data_lines = [
            (line_num, line)
            for line_num, line in data_lines[2:]
            if not re.match(r"^==\s*\d+\s+rows\s*==$", line)
        ]

    num_fields = len(header)

    for line_num, line in data_lines:
        if not line.strip():
            continue

        checked += 1
        rejected += validate_row(path, line_num, line, num_fields, system, pattern, settings)

    return checked, rejected


def validate_row(
    path: Path,
    line_num: int,
    line: str,
    num_fields: int,
    system: str,
    pattern: re.Pattern[str],
    settings: Settings,
) -> int:
    """Validate one row. Returns 1 if rejected, 0 if valid."""
    from ledgerkit.core import fields as csv_fields

    if system == "A":
        row_fields = csv_fields.split_record(line)
    else:
        row_fields = line.split(",")

    if len(row_fields) != num_fields:
        _log.warning(
            "%s line %d: expected %d fields, found %d",
            path.name,
            line_num,
            num_fields,
            len(row_fields),
        )
        return 1

    if system == "A":
        header = ["entry_id", "posted_on", "account", "memo", "amount", "currency"]
    elif system == "B":
        header = ["sys", "doc_no", "value_date", "acct", "descr", "amount", "cur"]
    else:
        header = ["ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy"]

    row = dict(zip(header, row_fields))

    # Check date format
    if system == "A":
        date_field = row.get("posted_on", "")
        date_format = "%Y-%m-%d"
    elif system == "B":
        date_field = row.get("value_date", "")
        date_format = "%Y-%m-%d"
    else:
        date_field = row.get("txn_date", "")
        date_format = "%d/%m/%Y"

    try:
        from datetime import datetime
        datetime.strptime(date_field.strip(), date_format)
    except ValueError:
        _log.warning(
            "%s line %d: date field %r does not match format %s",
            path.name,
            line_num,
            date_field,
            date_format,
        )
        return 1

    # Check amount is numeric
    if system == "A" or system == "C":
        amount_field = row.get("amount" if system == "A" else "gross_amount", "")
    else:
        amount_field = row.get("amount", "")

    try:
        from decimal import Decimal
        Decimal(amount_field.strip())
    except:
        _log.warning(
            "%s line %d: amount field %r is not a number",
            path.name,
            line_num,
            amount_field,
        )
        return 1

    # Check account code matches pattern
    if system == "A":
        code_field = row.get("account", "")
    elif system == "B":
        code_field = row.get("acct", "")
    else:
        code_field = row.get("ledger_acct", "")

    if not pattern.match(code_field.strip()):
        _log.warning(
            "%s line %d: account code %r does not match pattern %s",
            path.name,
            line_num,
            code_field,
            settings.account_code_pattern,
        )
        return 1

    return 0
