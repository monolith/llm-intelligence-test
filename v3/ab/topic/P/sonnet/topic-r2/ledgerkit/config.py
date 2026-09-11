"""Settings for a ledgerkit run.

Settings live in ``config/settings.toml`` next to this package.  That file is
checked in, is the same for every operator, and is not meant to be edited to
change what a single run does.

When a run needs different settings, point the ``LEDGERKIT_CONFIG`` environment
variable at another TOML file.  Anything that file leaves out falls back to the
value in ``config/settings.toml``, and anything both files leave out falls back
to :data:`DEFAULTS`, so an override file only has to carry the keys it changes.

:func:`load_settings` deliberately takes no arguments.  There is exactly one
place a caller can say where settings come from, and it is the environment.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from ledgerkit.log import get_logger

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "settings.toml"
CONFIG_ENV_VAR = "LEDGERKIT_CONFIG"

DEFAULTS: dict[str, dict[str, Any]] = {
    "report": {"decimals": 0, "unknown_account_label": "UNCLASSIFIED"},
    "reconcile": {"tolerance": 0.05},
    "validate": {"account_code_pattern": "^[0-9]{4}$"},
}

_log = get_logger(__name__)


@dataclass(frozen=True)
class Settings:
    """One resolved settings bundle."""

    decimals: int
    unknown_account_label: str
    tolerance: Decimal
    account_code_pattern: str
    source_path: Path

    def format_amount(self, value: Decimal) -> str:
        """Render an amount at the configured number of decimal places.

        The rounding mode is fixed by ``docs/CONVENTIONS.md``; this method does
        not choose one, it only lays out an already rounded value.
        """
        return f"{value:.{self.decimals}f}"

    def round_amount(self, value: Decimal) -> Decimal:
        """Round ``value`` to the configured number of decimal places, half to even."""
        exponent = Decimal(1).scaleb(-self.decimals)
        return value.quantize(exponent, rounding=ROUND_HALF_EVEN)


def config_path() -> Path:
    """Return the TOML file this run reads its settings from."""
    override = os.environ.get(CONFIG_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_PATH


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        _log.warning("settings file %s is missing; using built in defaults", path)
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _merge(base: dict[str, dict[str, Any]], overlay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {section: dict(values) for section, values in base.items()}
    for section, values in overlay.items():
        if not isinstance(values, dict):
            continue
        merged.setdefault(section, {})
        merged[section].update(values)
    return merged


def load_settings() -> Settings:
    """Read settings for this run.

    The layering is: built in defaults, then ``config/settings.toml``, then the
    file named by ``LEDGERKIT_CONFIG`` if there is one.
    """
    layered = _merge(DEFAULTS, _read_toml(DEFAULT_CONFIG_PATH))
    chosen = config_path()
    if chosen != DEFAULT_CONFIG_PATH:
        layered = _merge(layered, _read_toml(chosen))

    report = layered["report"]
    reconcile = layered["reconcile"]
    validate = layered["validate"]
    return Settings(
        decimals=int(report["decimals"]),
        unknown_account_label=str(report["unknown_account_label"]),
        tolerance=Decimal(str(reconcile["tolerance"])),
        account_code_pattern=str(validate["account_code_pattern"]),
        source_path=chosen,
    )
