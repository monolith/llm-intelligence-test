"""Put a pile of records into the shape the rest of the package expects.

:func:`normalize` is the last step of any read.  Readers hand it whatever they
managed to build; it cleans the fields up, puts the records in a stable order,
and hands back a new list.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from ledgerkit.core.records import Record, sort_key
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def _clean(record: Record) -> Record:
    return replace(
        record,
        record_id=record.record_id.strip(),
        source_system=record.source_system.strip().upper(),
        account_code=record.account_code.strip().upper(),
        description=" ".join(record.description.split()),
    )


def normalize(records: Iterable[Record], *, keep_refunds: bool = False) -> list[Record]:
    """Clean, filter and order a run of records.

    Field text is stripped, the system letter and the account code are upper
    cased, runs of whitespace inside a description collapse to one space, and the
    result comes back in :func:`~ledgerkit.core.records.sort_key` order.

    The ``keep_refunds`` switch decides what happens to postings with a negative
    amount.  Reports written for the FY-1 close were run without it, because the
    close packet treated a refund as an adjustment to a later period rather than
    a line of its own, and every caller since has inherited that default.  Pass
    ``keep_refunds=True`` when the output is meant to be the whole ledger.
    """
    cleaned: list[Record] = []
    dropped = 0
    for record in records:
        tidy = _clean(record)
        if tidy.amount < 0 and not keep_refunds:
            dropped += 1
            continue
        cleaned.append(tidy)
    if dropped:
        _log.info("normalize dropped %d refund row(s); pass keep_refunds=True to keep them", dropped)
    cleaned.sort(key=sort_key)
    return cleaned


def count_refunds(records: Iterable[Record]) -> int:
    """How many of these records are refunds."""
    return sum(1 for record in records if record.amount < 0)
