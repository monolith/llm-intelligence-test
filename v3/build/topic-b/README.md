# topic-b — shift-roster checker

`task/` is what the model under test receives: `SPEC-B.md`, an empty `roster/`
package and three public smoke tests. From inside `task/` (or any working copy)
the model runs `python -m pytest tests/`; on the untouched package all three
fail with an `ImportError`, because nothing is implemented yet. `hidden-tests/`
holds ten tests the model never sees, one behaviour each; run them against a
working copy with
`ROSTER_REPO=<path> PYTHONPATH=<path> python3 -m pytest hidden-tests/ -q --junitxml=out.xml`,
where `<path>` is the directory containing the `roster/` package — the suite
never imports `roster` into the pytest process, it shells out to
`python -m roster` and to short driver scripts, so a working copy that will not
even import fails the tests instead of crashing the run. `reference/` is a
correct solution (the same task directory plus an implementation) and passes
10/10 hidden and 3/3 public; it is the answer key, not something the model
sees. Any Python 3.12 with `pytest` importable will do — this fixture was built
and verified against
`/home/anatoly/llm-intelligence-test/v2/harness/.venv/bin/python`.
