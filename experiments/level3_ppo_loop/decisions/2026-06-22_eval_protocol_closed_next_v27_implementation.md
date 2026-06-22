# Eval Protocol Closed; Next Step Is V27 Implementation

Decision: hold_for_more_analysis

## Verdict

Do not launch `loop085` or any old automatic structural-search run yet.

The evaluator side of the loop is now wired for seed manifests, Wilson
confidence intervals, failure taxonomy, and dev-to-validation promotion. The
current validation anchor is:

- checkpoint: `level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final`
- seed split: `validation_unseen`
- seeds: `101-200`
- success rate: `0.20`
- Wilson 95% CI: `0.1334-0.2888`
- crash rate: `0.80`
- mean gates: `1.47`
- mean successful time: `6.858s`

The main remaining blocker is not another long run. The next useful work is a
runnable v27 teacher-retention implementation and a short 5M screen.

## Completed Prerequisites

- `scripts/level3_ppo_loop.py` can call the evaluator with:
  - `--seed-file`
  - `--seed-split-name`
  - `--confidence-interval wilson`
  - `--failure-taxonomy`
- Default loop evaluation now uses `dev_then_validation`:
  - screen checkpoints on `dev_seen`;
  - promote promising checkpoints to `validation_unseen`;
  - keep `final_locked` behind explicit unlock.
- `state.json` records `best_validation` and uses the validation anchor as the
  global checkpoint selector.
- `experiments/level3_ppo_loop/checkpoint_manifest.json` records local
  checkpoint paths and SHA256 values for loop052, loop071, and loop078.

## Required Next Lane

Implement and register v27 as a named structural lane before training:

`v27_teacher_retention_failure_correction_5m`

Contract:

- hard eval remains unchanged on `config/level3_dr.toml`;
- do not edit Level3 track geometry, gates, obstacles, or final evaluator seeds;
- teacher candidate: `loop052_final`;
- student/warm-start candidate: `loop078_final` when observation-compatible,
  otherwise implement explicit dual observation encoding;
- run short 5M screens with 1M checkpoint intervals;
- test beta arms `0.00`, `0.03`, and `0.10` only after the implementation
  passes dry-run and code validation;
- log all training and eval metrics to W&B project `ADR-PPO-Racing-Level3`;
- run analyzer and exactly three review agents after each completed arm before
  launching the next arm.

## Stop Rules

Stop and hold if:

- v27 teacher KL or retention data path cannot be implemented cleanly;
- teacher/student observation compatibility is unresolved;
- checkpoint artifacts are missing and cannot be restored locally or from an
  external registry;
- the 5M control arm cannot match basic retention behavior;
- validation success, crash, or mean gates regress below the loop052 validation
  anchor without a clear diagnostic reason.

