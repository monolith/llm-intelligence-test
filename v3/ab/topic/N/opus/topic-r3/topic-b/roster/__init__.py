"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API and the
``python -m roster check <file>`` command line.
"""

from roster._core import RosterError, Shift, find_conflicts, hours_by_person, parse_roster

__all__ = ["RosterError", "Shift", "find_conflicts", "hours_by_person", "parse_roster"]
