"""The project logger.

Every module in this package that wants to say something to the operator calls
:func:`get_logger` and logs through the object it returns.  Nothing else in the
package configures logging, and nothing else in the package writes to standard
error directly.

The handler is attached once, to the ``ledgerkit`` logger, and propagation to the
root logger is switched off, so a host application that embeds ledgerkit keeps
control of its own logging and does not get our records duplicated into its
handlers.

The level comes from ``LEDGERKIT_LOG_LEVEL`` and defaults to ``WARNING``.  Set it
to ``INFO`` when you want to watch an ingest run row by row.
"""

from __future__ import annotations

import logging
import os
import sys

ROOT_LOGGER_NAME = "ledgerkit"
LOG_FORMAT = "LEDGERKIT %(levelname)s %(name)s: %(message)s"
LEVEL_ENV_VAR = "LEDGERKIT_LOG_LEVEL"
DEFAULT_LEVEL = "WARNING"

_configured = False


def _resolve_level() -> int:
    """Turn the level named in the environment into a logging level number."""
    wanted = os.environ.get(LEVEL_ENV_VAR, DEFAULT_LEVEL).strip().upper()
    resolved = logging.getLevelNamesMapping().get(wanted)
    if resolved is None:
        return logging.WARNING
    return resolved


def configure() -> None:
    """Attach the one handler this package uses.  Safe to call repeatedly."""
    global _configured
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(_resolve_level())
    if _configured:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return the logger a module should use.

    ``name`` is normally ``__name__``.  Names that do not already sit under
    ``ledgerkit`` are moved there, so a logger is always reachable by the one
    handler this module installs.
    """
    configure()
    if name == ROOT_LOGGER_NAME or name.startswith(ROOT_LOGGER_NAME + "."):
        full_name = name
    else:
        full_name = f"{ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(full_name)
