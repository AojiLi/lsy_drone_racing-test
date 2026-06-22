# Level3 Structural PPO Training Plan

Decision: `launch_named_structural_lane`

Status: standing framework packet for the next Level3 PPO loop stage.

## Scope

The final acceptance target is `config/level3.toml`: success rate `>= 0.60`
and mean successful time `<= 7.0s`.

Do not modify Level3 track geometry or randomization. `config/level3_dr.toml`
may be used only as a labeled training-only robustness/domain-randomization
config. It is not the final acceptance gate.

Deployment remains:

```text
Level3 observation/history
  -> PPO actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, trajectory planner, or upper-level controller is part
of this plan.

## Current Evidence

The loop052/088/089/090 family plateaued well below the target. The validation
success seed union was only about 30/100, so even an oracle selecting among
those checkpoints would not reach the 60% target. Loop093, the first corrected
v30 semantics run, reached only `17/100` on final-target `level3.toml`.

This means the next loop should compare explicit structural training hypotheses,
not continue local reward-number or fixed-seed replay tweaks around loop052.

## Framework Priorities

1. PPO correctness and episode/action semantics.
2. Clean feed-forward PPO baseline with longer rollout.
3. Observation and return/value normalization support.
4. Asymmetric PPO: deployed actor uses normal observation; training critic may
   use privileged full state.
5. Gate-phase reset curriculum with competence gates.
6. Prioritized level replay over training track instances, not old transitions.
7. Recurrent actor GRU256 after reset semantics are proven clean.
8. Reward numbers only after the training distribution and value signal are
   trustworthy.
9. Speed optimization only after success approaches roughly 50%.

## Immediate Executable Lane

The first executable step is `v31a_longer_rollout_clean_ppo_5m`.

It keeps:

- v5 deployed observation;
- loop052 reward numbers;
- loop052 PPO numbers;
- loop052 final checkpoint as initialization;
- corrected v30 episode/reset/finish semantics;
- final hard eval on `config/level3.toml` validation seeds 101-200.

It changes only rollout geometry:

```text
old: 1024 envs x 32 steps  = 32768 samples/update
new:  256 envs x 128 steps = 32768 samples/update
```

At 50 Hz, this increases per-env rollout horizon from about `0.64s` to `2.56s`,
which should make gate approach, crossing, recovery, and obstacle-avoidance
credit assignment less bootstrap-heavy.

## Not Yet Implemented

These framework pieces require code support before training:

- actor observation RunningMeanStd;
- critic/return running scale;
- asymmetric privileged critic input and checkpoint metadata;
- gate-phase reset buffer with physically consistent state resets;
- competence-gated curriculum stages;
- prioritized level replay over train track seeds;
- tanh-squashed Gaussian PPO log-prob parity;
- GRU rerun with full hidden-state reset checks.

Do not mark a lane as one of these until the trainer/evaluator support exists
and focused tests or dry-runs prove it.

## Post-Run Rule

After every train/evaluate chunk:

- run `scripts/analyze_level3_ppo_trial.py`;
- use exactly three reviews: evaluator metrics, W&B/PPO diagnostics, and
  structure/research synthesis;
- write a main-agent decision packet before the next training chunk;
- commit and push code/state/analysis/decision changes to `aojili-test/main`;
- never accept W&B reward curves without hard evaluator evidence.
