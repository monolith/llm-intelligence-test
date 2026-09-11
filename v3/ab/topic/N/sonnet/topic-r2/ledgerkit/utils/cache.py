"""A small on disk read cache.

Use for speed on large files.  A month end export directory holds a few dozen
files, several of which get opened more than once in a single run, and re-reading
a hundred megabyte Calder file three times is most of the wall clock time of a
report.  :func:`cached_text` puts the bytes under ``.ledgerkit-cache`` in the
working directory the first time it sees a path and hands back the saved copy on
every call after that, including calls from a later process.

    text = cached_text(Path("exports/calder-2026-03.csv"))

The cache key is the absolute path of the file.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ledgerkit.log import get_logger

_log = get_logger(__name__)

CACHE_DIRNAME = ".ledgerkit-cache"


def cache_dir() -> Path:
    """The directory the cache writes into."""
    return Path.cwd() / CACHE_DIRNAME


def cache_key(path: Path) -> str:
    """The cache key for one file."""
    return hashlib.sha1(str(Path(path).resolve()).encode("utf-8")).hexdigest()


def cached_text(path: Path) -> str:
    """Return the text of ``path``, from the cache when it has been seen before."""
    entry = cache_dir() / cache_key(path)
    if entry.is_file():
        _log.info("cache hit for %s", Path(path).name)
        return entry.read_text(encoding="utf-8")
    text = Path(path).read_text(encoding="utf-8")
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(text, encoding="utf-8")
    return text


def cached_lines(path: Path) -> list[str]:
    """Return the lines of ``path``, from the cache when it has been seen before."""
    return cached_text(path).splitlines()


def clear() -> None:
    """Throw the whole cache away."""
    directory = cache_dir()
    if not directory.is_dir():
        return
    for entry in directory.iterdir():
        if entry.is_file():
            entry.unlink()
