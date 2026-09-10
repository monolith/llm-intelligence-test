"""Merge exports into one normalized file."""

from __future__ import annotations

from pathlib import Path

from ledgerkit.builders import build_record_from_a, build_record_from_b, build_record_from_c
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record, RECORD_COLUMNS
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, read_rows

_log = get_logger(__name__)


def ingest(files: list[str], out_path: str) -> int:
    """Merge export files into one normalized CSV.

    Args:
        files: List of export file paths.
        out_path: Where to write the normalized CSV.

    Returns:
        Exit code (0 on success).
    """
    settings = load_settings()
    records: list[Record] = []

    for file_path in files:
        path = Path(file_path)
        system = detect_system(path)
        raw_rows = read_rows(path)

        if system == "A":
            builder = build_record_from_a
        elif system == "B":
            builder = build_record_from_b
        else:
            builder = build_record_from_c

        for row in raw_rows:
            try:
                record = builder(row, settings.unknown_account_label)
                records.append(record)
            except Exception as exc:
                _log.warning("skipping row from %s: %s", path.name, exc)
                continue

    normalized = normalize(records, keep_refunds=True)

    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    from ledgerkit.core import fields

    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        handle.write(fields.join_record(list(RECORD_COLUMNS)) + "\n")
        for record in normalized:
            handle.write(fields.join_record(record.to_row()) + "\n")

    from ledgerkit.cli import emit
    emit(f"wrote={len(normalized)} to {out_path}")
    return 0
