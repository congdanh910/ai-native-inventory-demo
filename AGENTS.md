# Inventory

Command line stock keeping in Python 3.12, standard library only. Keep this file short; add a line whenever an AI role repeats a mistake.

## Commands
- Test: `python -m unittest discover -s tests -t .`
- Byte-compile check: `python -X pycache_prefix=/tmp/pyc -m compileall -q inventory`

## Structure
- `inventory/items.py`: pure item model. Every rule about items (validation, defaults, filtering, sorting, thresholds, history) lives here as functions that take and return values. No files, no printing, no clock.
- `inventory/store.py`: JSON persistence only. Loading validates records; files without newer fields must still load (fill defaults, never fail).
- `inventory/cli.py`: argparse wiring only; calls functions from `items.py` and `store.py` and prints.
- `tests/`: `unittest` tests. Test rules through `items.py`, persistence through `store.py` with a temporary directory, and commands through `cli.main(argv, out=...)`.

## Conventions
- Pass timestamps in (`now`) instead of reading the clock in `items.py`; tests use fixed ISO 8601 values.
- Raise `ValueError` with a clear message for invalid input; never silently convert or drop data.
- No third-party dependencies.

## Never
- Modify `.github/`, `.sdlc/` or anything outside `inventory/` and `tests/`.
