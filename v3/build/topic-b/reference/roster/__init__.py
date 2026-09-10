"""Shift-roster checker.

Public API: ``Shift``, ``RosterError``, ``parse_roster``, ``find_conflicts``
and ``hours_by_person``. The command line is ``python -m roster check <file>``.
"""

from .core import RosterError, Shift, find_conflicts, hours_by_person, parse_roster

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
