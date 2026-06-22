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

Loop094/v31a longer rollout briefly improved the corrected clean-PPO frontier
to `19/100`; loop097/v31d matured that branch to `20/100` at its 12M checkpoint.
Loop098 then continued the same branch toward a 30M-style horizon but regressed
to `19/100`, mean gates `1.63`, and crash rate `81%`.

This means the next loop should not continue local reward-number, fixed-seed
replay, or longer-rollout-only tweaks. It should move to the next named
structural support lane: asymmetric privileged Critic with strict Actor parity.

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

The immediate executable step is
`v32_asymmetric_privileged_critic_support_parity`.

This is not a training launch. It implements and validates support for:

- deployed Actor input: unchanged v5 observation/history prefix;
- deployed Actor output: unchanged roll/pitch/yaw/thrust PPO controller;
- training Critic input: Actor prefix plus training-only full-track state;
- checkpoint metadata: `critic_observation_mode`, `actor_observation_dim`, and
  `critic_observation_dim`;
- inference behavior: ignore Critic-only privileged weights and load Actor
  weights exactly as before.

Before any v32 training, the loop must generate a zero-update v32 checkpoint
from the loop097/v31d 12M best checkpoint and prove deterministic parity on
`validation_unseen_101_200` under `config/level3.toml`.

After that parity passes, the first training lane may be:

```text
v32_asymmetric_privileged_critic_clean_ppo_5m
```

It keeps v5 Actor observation, loop052 reward/PPO numbers, `256 envs x 128`
rollout geometry, corrected v30 semantics, and hard eval on
`config/level3.toml`. It changes only the training Critic input.

## Not Yet Implemented

These framework pieces require code support before training:

- separate actor/critic RunningMeanStd if normalization is combined with
  asymmetric Critic later;
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
