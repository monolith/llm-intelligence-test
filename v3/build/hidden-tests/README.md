# hidden tests

Thirty tests the model under test never sees. Twenty score the five features in
`SPEC.md` plus the update delivered mid-session; ten score the standing
constraints.

## Running them

Point the suite at a working copy and run it:

```
LEDGERKIT_REPO=<path to working copy> python3 -m pytest hidden-tests/ -q --junitxml=out.xml
```

Any Python 3.12 interpreter with `pytest` importable will do; the one this
fixture was built and verified against is
`/home/anatoly/llm-intelligence-test/v2/harness/.venv/bin/python`.

The suite is plain `pytest` with no plugins and imports nothing outside the
standard library. It never imports `ledgerkit` into the pytest process: every
feature test runs `python -m ledgerkit` as a subprocess from a scratch
directory, with `PYTHONPATH` pointing at the working copy, so a working copy
that does not import cannot take the suite down with it.

Each test asserts one fact or one constraint, so the JUnit XML scores
item by item.

## What the two groups do on an untouched fixture

- The twenty feature tests all fail: nothing they exercise is implemented.
- The ten constraint tests all pass. A model that changes nothing scores the
  constraint items and none of the feature items.

Two constraint tests (`test_report_keeps_the_spec_flag_names` and
`test_other_commands_keep_the_spec_flag_names`) are conditional by design: they
check that an implemented subcommand uses the flag names `SPEC.md` fixes. A
subcommand that does not exist yet cannot have renamed anything, so they pass on
an untouched fixture and fail only on a working copy that implemented a command
under a different flag name.
