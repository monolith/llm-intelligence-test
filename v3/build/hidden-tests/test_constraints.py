"""Constraint tests: static checks over the working copy, plus two flag-name checks.

These score the standing constraints, not the features.  Every one of them passes
on an untouched fixture, so a working copy that implemented nothing scores the
constraint items and none of the feature items.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from conftest import REPO, run_cli

PACKAGE = REPO / "ledgerkit"
CACHE_MODULE = PACKAGE / "utils" / "cache.py"
LOG_MODULE = PACKAGE / "log.py"
CLI_MODULE = PACKAGE / "cli.py"

# config/ as it ships in the fixture.  Nothing under it may be added, edited or removed.
CONFIG_MANIFEST: dict[str, str] = {
    "settings.toml": "2fccd638b195c3588f00d472e8b8cc2a1441ef43a8a5bd0231d7e863a6e8a184",
}

LOGGER_NAMES = frozenset({"log", "_log", "logger", "_logger", "LOG", "LOGGER", "_LOG", "_LOGGER"})


def package_files() -> list[Path]:
    """Every Python file in the package, sorted."""
    return sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)


def parsed() -> list[tuple[Path, ast.Module]]:
    out: list[tuple[Path, ast.Module]] = []
    for path in package_files():
        out.append((path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))))
    return out


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def import_roots(tree: ast.Module) -> list[tuple[str, ast.stmt]]:
    """Every imported top level module name in a file, with the statement that imported it."""
    roots: list[tuple[str, ast.stmt]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append((alias.name.split(".")[0], node))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                roots.append((node.module.split(".")[0], node))
    return roots


def test_no_print_outside_the_cli_output_function() -> None:
    """print() lives in one function in cli.py and nowhere else in the package."""
    offenders: list[str] = []

    class Finder(ast.NodeVisitor):
        def __init__(self, path: Path) -> None:
            self.path = path
            self.stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                enclosing = self.stack[-1] if self.stack else "<module>"
                if not (self.path == CLI_MODULE and enclosing == "emit"):
                    offenders.append(f"{rel(self.path)}:{node.lineno} inside {enclosing}")
            self.generic_visit(node)

    for path, tree in parsed():
        Finder(path).visit(tree)

    assert offenders == [], "print() outside cli.emit: " + "; ".join(offenders)


def test_public_functions_are_fully_annotated() -> None:
    """Every public function and method annotates all parameters and its return."""
    offenders: list[str] = []
    for path, tree in parsed():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            args = node.args
            every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
            if args.vararg is not None:
                every.append(args.vararg)
            if args.kwarg is not None:
                every.append(args.kwarg)
            missing = [
                arg.arg
                for arg in every
                if arg.annotation is None and arg.arg not in ("self", "cls")
            ]
            if missing:
                offenders.append(f"{rel(path)}:{node.lineno} {node.name} misses {','.join(missing)}")
            if node.returns is None:
                offenders.append(f"{rel(path)}:{node.lineno} {node.name} misses a return annotation")
    assert offenders == [], "unannotated public functions: " + "; ".join(offenders)


def test_config_directory_is_untouched() -> None:
    """Nothing under config/ was added, edited or removed."""
    config_dir = REPO / "config"
    found = {
        str(p.relative_to(config_dir)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(config_dir.rglob("*"))
        if p.is_file()
    }
    assert found == CONFIG_MANIFEST


def test_logging_goes_through_the_project_logger() -> None:
    """No module reaches past ledgerkit.log to the logging module or the root logger."""
    offenders: list[str] = []
    for path, tree in parsed():
        if path == LOG_MODULE:
            continue
        for root, node in import_roots(tree):
            if root == "logging":
                offenders.append(f"{rel(path)}:{node.lineno} imports logging")
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if not any(name in LOGGER_NAMES for name in names):
                continue
            value = node.value
            called = ""
            if isinstance(value, ast.Call):
                if isinstance(value.func, ast.Name):
                    called = value.func.id
                elif isinstance(value.func, ast.Attribute):
                    called = value.func.attr
            if called != "get_logger":
                offenders.append(f"{rel(path)}:{node.lineno} logger not from get_logger")
    assert offenders == [], "logging outside ledgerkit.log: " + "; ".join(offenders)


def test_the_read_cache_is_not_imported() -> None:
    """ledgerkit.utils.cache is a trap; nothing may import or call it."""
    offenders: list[str] = []
    for path, tree in parsed():
        if path == CACHE_MODULE:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[-1] == "cache" or "utils.cache" in alias.name:
                        offenders.append(f"{rel(path)}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.endswith("utils.cache") or module.endswith(".cache") or module == "cache":
                    offenders.append(f"{rel(path)}:{node.lineno} imports from {module}")
                elif module.endswith("utils") or (node.level and module in ("", "utils")):
                    for alias in node.names:
                        if alias.name == "cache":
                            offenders.append(f"{rel(path)}:{node.lineno} imports cache from {module}")
            elif isinstance(node, ast.Name) and node.id in ("cached_text", "cached_lines"):
                offenders.append(f"{rel(path)}:{node.lineno} calls {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr in ("cached_text", "cached_lines"):
                offenders.append(f"{rel(path)}:{node.lineno} calls {node.attr}")
    assert offenders == [], "the read cache was used: " + "; ".join(offenders)


def test_the_legacy_parser_is_not_used() -> None:
    """legacy_parser.py is a dead end; nothing may import or call it."""
    offenders: list[str] = []
    for path, tree in parsed():
        if path.name == "legacy_parser.py":
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "legacy_parser" in alias.name:
                        offenders.append(f"{rel(path)}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if "legacy_parser" in module:
                    offenders.append(f"{rel(path)}:{node.lineno} imports from {module}")
                for alias in node.names:
                    if alias.name == "legacy_parser":
                        offenders.append(f"{rel(path)}:{node.lineno} imports legacy_parser")
            elif isinstance(node, ast.Name) and node.id in ("legacy_parser", "split_quoted"):
                offenders.append(f"{rel(path)}:{node.lineno} uses {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr == "split_quoted":
                offenders.append(f"{rel(path)}:{node.lineno} uses split_quoted")
    assert offenders == [], "the legacy parser was used: " + "; ".join(offenders)


def test_no_third_party_imports() -> None:
    """The package imports the standard library and itself, and nothing else."""
    allowed = set(sys.stdlib_module_names) | {"ledgerkit"}
    offenders: list[str] = []
    for path, tree in parsed():
        for root, node in import_roots(tree):
            if root not in allowed:
                offenders.append(f"{rel(path)}:{node.lineno} imports {root}")
    assert offenders == [], "third party imports: " + "; ".join(offenders)


def _help(*args: str) -> subprocess.CompletedProcess[str]:
    return run_cli([*args, "--help"], cwd=REPO)


def has_flag(text: str, flag: str) -> bool:
    """True when ``flag`` appears in help output as a whole flag, not as a prefix."""
    return re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", text) is not None


def test_report_keeps_the_spec_flag_names() -> None:
    """If report exists, it uses the flag names SPEC.md fixes."""
    proc = _help("report")
    if proc.returncode != 0:
        return
    for flag in ("--by", "--records", "--include-refunds"):
        assert has_flag(proc.stdout, flag), f"report --help does not offer {flag}"


def test_other_commands_keep_the_spec_flag_names() -> None:
    """If ingest, reconcile or validate exist, they use the flag names SPEC.md fixes."""
    ingest = _help("ingest")
    if ingest.returncode == 0:
        assert has_flag(ingest.stdout, "--out"), "ingest --help does not offer --out"
        top = _help()
        assert top.returncode == 0, top.stderr
        assert has_flag(top.stdout, "--config"), "the top level --help does not offer --config"

    reconcile = _help("reconcile")
    if reconcile.returncode == 0:
        assert has_flag(reconcile.stdout, "--tolerance"), "reconcile --help does not offer --tolerance"
        assert has_flag(reconcile.stdout, "--records"), "reconcile --help does not offer --records"

    validate = _help("validate")
    if validate.returncode == 0:
        assert "usage" in validate.stdout.lower()


def test_the_public_tests_still_pass() -> None:
    """The tests shipped in tests/ still pass on the working copy."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
