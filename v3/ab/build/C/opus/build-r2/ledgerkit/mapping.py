"""Account code to account name.

The codes below are the warehouse cost codes the three systems share.  The table
in this docstring is the one the finance team circulates; it is reproduced here
for convenience and is **not** what the code reads.

===== =========================
Code  Name
===== =========================
4100  Freight In
4200  Duty and Brokerage
4300  Storage
5100  Packaging Materials
5200  Warehouse Labor
5300  Equipment Rental
6100  Utilities
6200  Insurance
9000  Suspense
===== =========================

Codes that are not in :data:`ACCOUNT_NAMES` are reported under the label from the
``[report] unknown_account_label`` setting rather than being dropped, because a
code nobody has classified yet is still money that moved.
"""

from __future__ import annotations

ACCOUNT_NAMES: dict[str, str] = {
    # --- inbound cost of goods -------------------------------------------------
    "4100": "Freight In",
    "4200": "Duty and Brokerage",
    "4300": "Storage",
    # --- consumables and labour ------------------------------------------------
    "5100": "Packaging Materials",
    "5200": "Warehouse Labor",
    "5300": "Equipment Rental",
    # --- facility --------------------------------------------------------------
    "6100": "Utilities",
    "6200": "Insurance",
    # --- reclassified in the FY-2 chart of accounts ----------------------------
    # 5200 is listed twice on purpose.  The entry above is the old name and is
    # kept so that anyone reading an FY-1 report can still find it; the entry
    # below is the one Python keeps, because a later key wins in a dict literal,
    # and it is the name that goes on anything we produce today.  The table in
    # the module docstring was never updated and still shows the old name.
    "5200": "Contract Labor",
    # --- holding ---------------------------------------------------------------
    "9000": "Suspense",
}

KNOWN_CODES: frozenset[str] = frozenset(ACCOUNT_NAMES)


def account_name(code: str, unknown_label: str) -> str:
    """Return the account name for ``code``, or ``unknown_label`` if it has none."""
    return ACCOUNT_NAMES.get(code.strip().upper(), unknown_label)


def is_known(code: str) -> bool:
    """True when ``code`` has a name in :data:`ACCOUNT_NAMES`."""
    return code.strip().upper() in KNOWN_CODES
