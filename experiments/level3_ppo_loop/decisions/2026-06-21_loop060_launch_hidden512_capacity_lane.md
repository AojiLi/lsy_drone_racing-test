# Loop060 Decision: Launch Hidden512 Capacity Lane

## Decision

`launch_named_structural_lane`

## Approved Lane

- Structural hypothesis: `v10_hidden512_warmstart_capacity_from_loop052`
- Proposal name: `structural_v10_hidden512_warmstart_capacity_from_loop052_30m`
- Target hard eval: `config/level3_dr.toml`
- Track boundary: do not modify Level3 track geometry or randomization.

## Evidence

- loop060 tested v9 gate-aperture-margin observation from loop052 but did not
  beat the global best. Best loop060 hard eval was 15% success, 85% crash,
  mean gates 1.3, mean successful time 6.393s.
- Global best remains loop052 with 20% success, 80% crash, mean gates 1.4,
  mean successful time 6.975s.
- loop060 W&B curves did not show gate/finish conversion; approximate KL and
  clip fraction stayed very small.
- Three research/review agents agreed that network capacity is a reasonable
  structural hypothesis, but should be tested as a bounded lane rather than by
  adding recurrent/attention architecture immediately.

## Implementation Contract

- Start from loop052 checkpoint.
- Use v9 gate-aperture-margin observation.
- Keep reward numbers, controller settings, and PPO update settings equal to
  the v9 lane except for `hidden_dim=512`.
- Use explicit hidden-dim block-copy warm-start from hidden_dim=256 to
  hidden_dim=512.
- Run a 30M screening chunk with 5M checkpoint interval.
- After completion, run `scripts/analyze_level3_ppo_trial.py`, then perform the
  required evaluator, W&B/PPO, and structure/research reviews before launching
  another training chunk.

## Follow-Up Tuning Contract

The hidden512 screen is not a one-off fixed-reward endpoint. If the first v10
screening run does not meet the target, the next Codex-supervised loop may keep
the same network size and observation layout, select the best evaluated
hidden_dim=512 checkpoint, and tune reward numbers or bounded PPO/reward
hyperparameters inside that hidden512 regime.

Use the follow-up structural lane
`v10_hidden512_reward_search_from_best` for this purpose. It must not fall back
to hidden_dim=256 checkpoints, and it must still hard-evaluate on
`config/level3_dr.toml`.

## Promotion Rule

If any checkpoint exceeds loop052's 20% success rate or materially improves
mean gates beyond 1.4 while keeping mean successful time under 7.0s, mature the
same capacity lane toward 60M before rejecting it.
