"""Shift-roster checker.

Reads a plain-text roster, finds shifts of one person that overlap, and totals
hours per person. See ``SPEC-B.md`` for the format and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

from roster.core import RosterError, Shift, find_conflicts, hours_by_person, parse_roster

__all__ = ["RosterError", "Shift", "find_conflicts", "hours_by_person", "parse_roster"]
