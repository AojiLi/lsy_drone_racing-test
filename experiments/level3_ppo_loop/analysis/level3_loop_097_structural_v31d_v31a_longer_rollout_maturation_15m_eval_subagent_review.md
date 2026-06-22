# Evaluator Metrics Review: loop097 / v31d

## Key Finding

v31d is a marginal but real improvement over loop094/v31a. It does not meet the
target.

## Evidence

- loop094/v31a best: `19/100` success, mean successful time `6.8758s`, crash
  `81%`, mean gates `1.55`.
- loop097/v31d best: `20/100` success, mean successful time `7.055s`, crash
  `80%`, mean gates `1.66`.
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt`.
- 14M tied success at `20%` but was slower and slightly lower on mean gates;
  final fell back to `19%`.
- Failures remain contact-driven: `80` contacts, likely `bounds_or_ground`.
  Failure rates are concentrated at gates 0, 1, and 2: `30%`, `20%`, `27%`.

## Recommended Next Action

Continue the same hypothesis from the 12M best checkpoint with milestone-aware
hard eval. The evidence is weak but positive enough under the step-curve rule
to mature before rejecting. Do not modify track geometry.

