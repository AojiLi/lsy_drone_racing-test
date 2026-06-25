# V54 Reference Tracker Resume Checker Gate

Created: 2026-06-25

Result: `ALL GREEN`

Purpose: verify the minimal `--initial-model-path` support before running the
v54 hover -> point -> gate-aperture curriculum.

## Evidence

Checker verified:

- `git diff --check -- lsy_drone_racing/control/train_level3_reference_tracker_ppo.py`
  passed with no output;
- `pixi run -e gpu python -m py_compile ...` passed for the v54 trainer and
  dependent files;
- `pixi run -e gpu ruff check ...` returned `All checks passed!`;
- `git diff --exit-code -- config/level3.toml` passed with no output.

## Code Inspection

- `--initial-model-path` is present in
  `lsy_drone_racing/control/train_level3_reference_tracker_ppo.py`.
- Resume uses `load_tracker_checkpoint` with observation-dimension validation.
- Global-step offset is read from checkpoint metadata.
- The script does not launch training on import; training still runs only under
  the CLI `main()` guard.

## Residual Risk

This is a weight-only resume. Adam optimizer state is intentionally not resumed
for this small curriculum preflight.
