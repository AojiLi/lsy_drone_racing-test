# Correct Final Target to level3.toml

Decision: `hold_for_more_analysis`

Status: target-protocol correction. This packet does not authorize training.

## Correction

The final Level3 target is `config/level3.toml`, not `config/level3_dr.toml`.

`config/level3_dr.toml` is a domain-randomized sim-to-real robustness/training
configuration. It may be useful as a named training curriculum or robustness
lane, but it is not the final acceptance environment.

## Consequences

- Final hard eval, target-met checks, and future promoted `best` checkpoints
  must use `config/level3.toml`.
- Historical `level3_dr.toml` metrics remain useful as robustness evidence, but
  they are not directly comparable to final-target `level3.toml` metrics.
- The existing loop052 `level3_dr.toml` validation anchor must be relabeled as a
  DR robustness anchor, not the final target baseline.
- Before v30 training, establish a fresh loop052 old-inference baseline on
  `config/level3.toml` with `validation_unseen` seeds 101-200.
- The v30 zero-update parity gate must compare repaired/squashed inference
  against that `level3.toml` loop052 baseline.

## Boundary

Do not edit `config/level3.toml` track geometry or randomization to improve
metrics. If `level3_dr.toml` or another alternate config is used for training,
the lane must explicitly label it as training-only and still evaluate on
unchanged `config/level3.toml`.
