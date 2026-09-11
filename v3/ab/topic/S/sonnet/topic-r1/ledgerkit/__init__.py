"""ledgerkit -- merge and report on ledger exports from three legacy systems.

The three systems are referred to throughout by their letter:

* **A** -- Ardent, the oldest of the three.  Writes a commented preamble, then a
  header row, then comma separated rows with quoted memo fields.
* **B** -- Borough.  One header row, then comma separated rows.  Every row starts
  with a literal ``B`` in the ``sys`` column.
* **C** -- Calder.  A one line banner, a header row, comma separated rows, and a
  trailing row count line.

Nothing in this package talks to any of those systems directly.  It reads the
files they drop into an export directory and turns them into one normalized set
of records.
"""

from __future__ import annotations

__version__ = "0.4.1"

__all__ = ["__version__"]
