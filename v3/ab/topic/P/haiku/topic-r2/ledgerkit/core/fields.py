"""Delimiter aware field splitting and joining.

This is the splitter the current readers use.  It follows the same quoting rules
the three export systems follow: a field may be wrapped in double quotes, a
quoted field may contain the delimiter, and a literal double quote inside a
quoted field is written twice.

    >>> split_record('A-1,2026-01-03,"Rebill, ""Q1"", carrier",12.00')
    ['A-1', '2026-01-03', 'Rebill, "Q1", carrier', '12.00']

The standard library ``csv`` module does the same job for whole files.  This
module exists because the readers need to work a line at a time, after they have
thrown away preamble and trailer lines that ``csv`` would hand back as rows.
"""

from __future__ import annotations

QUOTE = '"'


def split_record(line: str, delimiter: str = ",") -> list[str]:
    """Split one delimited line into its fields.

    Quoted fields keep any delimiter inside them, and a doubled quote inside a
    quoted field becomes one quote character in the result.  Whitespace around an
    unquoted field is kept as written; export systems have been known to mean it.
    """
    fields: list[str] = []
    current: list[str] = []
    in_quotes = False
    index = 0
    length = len(line)

    while index < length:
        char = line[index]
        if in_quotes:
            if char == QUOTE:
                if index + 1 < length and line[index + 1] == QUOTE:
                    current.append(QUOTE)
                    index += 2
                    continue
                in_quotes = False
                index += 1
                continue
            current.append(char)
            index += 1
            continue

        if char == QUOTE and not current:
            in_quotes = True
            index += 1
            continue
        if char == delimiter:
            fields.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    fields.append("".join(current))
    return fields


def join_record(fields: list[str], delimiter: str = ",") -> str:
    """Join fields back into one line, quoting the ones that need it."""
    out: list[str] = []
    for field in fields:
        if delimiter in field or QUOTE in field or "\n" in field:
            out.append(QUOTE + field.replace(QUOTE, QUOTE * 2) + QUOTE)
        else:
            out.append(field)
    return delimiter.join(out)


def has_quoted_field(line: str) -> bool:
    """True when ``line`` contains a quote character at all."""
    return QUOTE in line
