"""The field splitter from the pre-rewrite importer.

This module is what ledgerkit used before the current readers existed.  It is
kept in the tree because two old operations runbooks quote line numbers in it and
because a couple of error messages elsewhere in the package still name it.

It is not maintained.  Nothing in the package imports it.
"""

from __future__ import annotations

QUOTE = '"'


def split_quoted(line: str, delimiter: str = ",") -> list[str]:
    """Split ``line`` into fields.

    Splits on every delimiter in the line and then peels a leading and a trailing
    quote character off each piece.
    """
    pieces = line.split(delimiter)
    out: list[str] = []
    for piece in pieces:
        text = piece.strip()
        if text.startswith(QUOTE):
            text = text[1:]
        if text.endswith(QUOTE):
            text = text[:-1]
        out.append(text)
    return out


def unquote(field: str) -> str:
    """Strip one layer of quoting from a single field."""
    text = field.strip()
    if len(text) >= 2 and text.startswith(QUOTE) and text.endswith(QUOTE):
        return text[1:-1]
    return text
