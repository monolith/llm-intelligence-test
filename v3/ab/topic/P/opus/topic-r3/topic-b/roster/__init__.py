"""Shift-roster checker.

Reads a plain-text roster of one shift per line, finds the shifts that clash,
and totals hours per person.  See ``SPEC-B.md`` for the format and the
``python -m roster check <file>`` command line.

    >>> from roster import parse_roster, hours_by_person
    >>> hours_by_person(parse_roster("2026-05-01 22:00-06:00 Ann Diaz\\n"))
    {'Ann Diaz': 8.0}
"""

from __future__ import annotations

from roster.core import RosterError, Shift, find_conflicts, hours_by_person, parse_roster

__all__ = ["RosterError", "Shift", "find_conflicts", "hours_by_person", "parse_roster"]
