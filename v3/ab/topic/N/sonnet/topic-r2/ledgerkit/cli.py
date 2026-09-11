"""The ``python -m ledgerkit`` command line.

Only two subcommands are wired up so far, ``version`` and ``inspect``.  The rest
of the commands the operations team has asked for are written up in ``SPEC.md``
and are not implemented yet.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, read_records, write_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

PARSER_BY_SYSTEM = {
    "A": system_a,
    "B": system_b,
    "C": system_c,
}

DATE_FIELD_BY_SYSTEM = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
AMOUNT_FIELD_BY_SYSTEM = {"A": "amount", "B": "amount", "C": "gross_amount"}
ACCOUNT_FIELD_BY_SYSTEM = {"A": "account", "B": "acct", "C": "ledger_acct"}

DEFAULT_RECORDS_PATH = "out/records.csv"


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="read settings from PATH instead of config/settings.toml, for this run only",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write the normalized CSV"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", choices=("account", "month"), required=True, help="how to group totals")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; totals always include refunds",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=Decimal, default=None, metavar="N", help="dollars of disagreement to tolerate"
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in export files")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def cmd_version(args: argparse.Namespace) -> int:
    """Print the package version and the settings file in force."""
    settings = load_settings()
    emit(f"{PROGRAM_NAME} {__version__}")
    emit(f"settings={settings.source_path}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Print the format, size and column names of each export named on the command line."""
    status = 0
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            lines = count_data_lines(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot inspect %s: %s", path, exc)
            status = 1
            continue
        emit(f"file={path.name}")
        emit(f"system={system}")
        emit(f"data_lines={lines}")
        emit("columns=" + ",".join(COLUMNS_BY_SYSTEM[system]))
    return status


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge any number of exports, from any of the three systems, into one normalized CSV."""
    settings = load_settings()
    all_records = []
    failure = False
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            module = PARSER_BY_SYSTEM[system]
            rows = module.read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            failure = True
            continue
        for row in rows:
            all_records.append(module.to_record(row, unknown_label=settings.unknown_account_label))

    if failure:
        return 1

    records = normalize(all_records, keep_refunds=True)
    out_path = Path(args.out)
    write_records(out_path, records)
    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month.

    Totals always include refunds; ``--include-refunds`` is accepted so that
    scripts written for the old default keep working, but it has no effect.
    """
    settings = load_settings()
    records = read_records(Path(args.records))

    if args.by == "account":
        totals: dict[str, Decimal] = {}
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
            names[record.account_code] = record.account_name
        emit("account_code;account_name;total")
        for code in sorted(totals):
            emit(f"{code};{names[code]};{settings.format_amount(totals[code])}")
    else:
        totals = {}
        for record in records:
            month = record.month()
            totals[month] = totals.get(month, Decimal(0)) + record.amount
        emit("month;total")
        for month in sorted(totals):
            emit(f"{month};{settings.format_amount(totals[month])}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree on the total."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = read_records(Path(args.records))

    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = totals.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches = 0
    for account_code, month in sorted(totals):
        by_system = totals[(account_code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread <= tolerance:
            continue
        mismatches += 1
        columns = " ".join(
            f"{system}={by_system[system]:.2f}" if system in by_system else f"{system}=-" for system in SYSTEMS
        )
        emit(f"MISMATCH {account_code} {month} spread={spread:.2f} {columns}")
    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row, rejecting any that are malformed."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked = 0
    rejected = 0
    read_failure = False

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            module = PARSER_BY_SYSTEM[system]
            header = module.read_header(path)
            data_lines = list(module.iter_data_lines(path))
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            read_failure = True
            continue

        date_field = DATE_FIELD_BY_SYSTEM[system]
        amount_field = AMOUNT_FIELD_BY_SYSTEM[system]
        account_field = ACCOUNT_FIELD_BY_SYSTEM[system]

        for number, line in data_lines:
            checked += 1
            values = module.split_fields(line)
            if len(values) != len(header):
                _log.warning(
                    "%s line %d: expected %d fields, found %d", path.name, number, len(header), len(values)
                )
                rejected += 1
                continue

            row = dict(zip(header, values, strict=True))
            bad = False
            try:
                module.parse_date(row[date_field])
            except LedgerParseError as exc:
                _log.warning("%s line %d: %s", path.name, number, exc)
                bad = True
            try:
                module.parse_amount(row[amount_field])
            except LedgerParseError as exc:
                _log.warning("%s line %d: %s", path.name, number, exc)
                bad = True
            if not pattern.fullmatch(row[account_field].strip()):
                _log.warning(
                    "%s line %d: account code %r does not match %s",
                    path.name,
                    number,
                    row[account_field],
                    settings.account_code_pattern,
                )
                bad = True
            if bad:
                rejected += 1

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or read_failure else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    previous_config = os.environ.get(CONFIG_ENV_VAR)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = str(Path(args.config))
    try:
        handler = args.handler
        return int(handler(args))
    finally:
        if args.config:
            if previous_config is None:
                os.environ.pop(CONFIG_ENV_VAR, None)
            else:
                os.environ[CONFIG_ENV_VAR] = previous_config
