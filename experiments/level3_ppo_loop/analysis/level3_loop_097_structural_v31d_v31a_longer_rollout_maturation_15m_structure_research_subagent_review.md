# Structure / Research Review: loop097 / v31d

## Key Finding

Continue v31d to a 30M-style maturation before moving to v32 trainer-support
work.

## Evidence

- loop097/v31d expands the v31a frontier from `19%` success and `1.55` mean
  gates to `20%` success and `1.66` mean gates.
- The improvement is thin, so it does not justify jumping to a 60M continuation
  yet.
- The improvement is real enough to satisfy the prior condition: do not reject
  when a branch adds success seeds or mean-gate expansion.

## Recommended Next Lane

`v31d_longer_rollout_maturation_from_loop097_12m_to_30m`

Start from loop097 12M best, keep:

- v5 observation;
- loop052 reward/PPO numbers;
- corrected v30 semantics;
- no observation/return normalization;
- `256 envs x 128 steps`;
- hard eval on unchanged `config/level3.toml`.

Promote toward 60M only if the 30M-style hard eval beats loop097's `20%` /
`1.66` frontier or adds meaningful new success seeds / lower crash. Otherwise
move to v32 support work or a named reward adjustment lane.

