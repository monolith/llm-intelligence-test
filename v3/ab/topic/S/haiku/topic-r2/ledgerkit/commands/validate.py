"""Validate export files for malformed rows."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.fields import split_record
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def validate_file_a(path: Path, settings: Settings) -> tuple[int, int]:
    """Validate a System A export file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header = None
    header_line = 0
    data_lines = 0
    rejected = 0

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue

        if header is None:
            header = split_record(line)
            header_line = line_num
            continue

        data_lines += 1

        # Check field count
        fields = split_record(line)
        if len(fields) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d",
                path.name,
                line_num,
                len(header),
                len(fields),
            )
            rejected += 1
            continue

        row = dict(zip(header, fields))

        # Check date
        try:
            date.fromisoformat(row["posted_on"])
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable date", path.name, line_num)
            rejected += 1
            continue

        # Check amount
        try:
            float(row["amount"])
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable amount", path.name, line_num)
            rejected += 1
            continue

        # Check account code
        try:
            if not re.match(settings.account_code_pattern, row["account"]):
                _log.warning("%s line %d: account code does not match pattern", path.name, line_num)
                rejected += 1
        except KeyError:
            _log.warning("%s line %d: unparseable account code", path.name, line_num)
            rejected += 1

    return data_lines, rejected


def validate_file_b(path: Path, settings: Settings) -> tuple[int, int]:
    """Validate a System B export file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header = None
    data_lines = 0
    rejected = 0

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped:
            continue

        if header is None:
            header = line.split(",")
            continue

        data_lines += 1

        fields = line.split(",")
        if len(fields) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d",
                path.name,
                line_num,
                len(header),
                len(fields),
            )
            rejected += 1
            continue

        row = dict(zip(header, fields))

        # Check date
        try:
            date.fromisoformat(row["value_date"])
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable date", path.name, line_num)
            rejected += 1
            continue

        # Check amount
        try:
            int(row["amount"])
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable amount", path.name, line_num)
            rejected += 1
            continue

        # Check account code
        try:
            if not re.match(settings.account_code_pattern, row["acct"]):
                _log.warning("%s line %d: account code does not match pattern", path.name, line_num)
                rejected += 1
        except KeyError:
            _log.warning("%s line %d: unparseable account code", path.name, line_num)
            rejected += 1

    return data_lines, rejected


def validate_file_c(path: Path, settings: Settings) -> tuple[int, int]:
    """Validate a System C export file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header = None
    data_lines = 0
    rejected = 0
    seen_banner = False

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped:
            continue

        if not seen_banner:
            if not stripped.startswith("CALDER EXPORT"):
                _log.warning("%s line %d: missing Calder banner", path.name, line_num)
                return 0, 1
            seen_banner = True
            continue

        # Skip trailer
        if stripped.startswith("=="):
            continue

        if header is None:
            header = line.split(",")
            continue

        data_lines += 1

        fields = line.split(",")
        if len(fields) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d",
                path.name,
                line_num,
                len(header),
                len(fields),
            )
            rejected += 1
            continue

        row = dict(zip(header, fields))

        # Check date (DD/MM/YYYY format)
        try:
            parts = row["txn_date"].split("/")
            if len(parts) != 3:
                raise ValueError("wrong format")
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable date", path.name, line_num)
            rejected += 1
            continue

        # Check amount
        try:
            float(row["gross_amount"])
        except (ValueError, KeyError):
            _log.warning("%s line %d: unparseable amount", path.name, line_num)
            rejected += 1
            continue

        # Check account code
        try:
            if not re.match(settings.account_code_pattern, row["ledger_acct"]):
                _log.warning("%s line %d: account code does not match pattern", path.name, line_num)
                rejected += 1
        except KeyError:
            _log.warning("%s line %d: unparseable account code", path.name, line_num)
            rejected += 1

    return data_lines, rejected


def validate(file_paths: list[str], settings: Settings) -> int:
    """Validate export files.

    Returns exit code 0 if all valid, exit code 2 if any rejected.
    """
    total_checked = 0
    total_rejected = 0

    for file_path in file_paths:
        path = Path(file_path)

        try:
            system = detect_system(path)
        except (LedgerParseError, OSError):
            return 2

        try:
            if system == "A":
                checked, rejected = validate_file_a(path, settings)
            elif system == "B":
                checked, rejected = validate_file_b(path, settings)
            else:  # system == "C"
                checked, rejected = validate_file_c(path, settings)

            total_checked += checked
            total_rejected += rejected
        except Exception:
            return 2

    print(f"checked={total_checked} rejected={total_rejected}")

    return 2 if total_rejected > 0 else 0
