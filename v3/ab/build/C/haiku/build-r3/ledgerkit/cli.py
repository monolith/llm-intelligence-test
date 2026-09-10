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
from collections.abc import Sequence
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}


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
    parser.add_argument("--config", metavar="PATH", help="path to custom settings file")

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument("--out", default="out/records.csv", metavar="PATH", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser(
        "report", help="print totals by account or month"
    )
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="grouping type")
    report_parser.add_argument("--records", default="out/records.csv", metavar="PATH", help="normalized records file")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report where systems disagree"
    )
    reconcile_parser.add_argument("--records", default="out/records.csv", metavar="PATH", help="normalized records file")
    reconcile_parser.add_argument("--tolerance", type=float, metavar="N", help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows"
    )
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to validate")
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
    """Merge exports into one normalized file."""
    from ledgerkit.commands.ingest import ingest
    return ingest(args.files, args.out)


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    from ledgerkit.commands.report import report
    return report(args.by, args.records)


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report where systems disagree."""
    from decimal import Decimal
    from ledgerkit.commands.reconcile import reconcile

    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    return reconcile(args.records, tolerance)


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    from ledgerkit.commands.validate import validate
    return validate(args.files)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    import os
    from ledgerkit.config import CONFIG_ENV_VAR

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config

    handler = args.handler
    return int(handler(args))
