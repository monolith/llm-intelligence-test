"""Entry point for ``python -m ledgerkit``."""

from __future__ import annotations

import sys

from ledgerkit.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
