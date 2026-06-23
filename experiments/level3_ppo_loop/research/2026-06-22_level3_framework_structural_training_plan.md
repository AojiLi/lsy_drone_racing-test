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

v32 asymmetric privileged Critic support and parity passed, but its bounded
training evidence did not expand the frontier. loop099 reached `19/100`,
`1.66` mean gates, and `81%` crash; loop100 matured from the loop099 3M best
to about 18M and still reached only `19/100`, `1.65` mean gates, and `81%`
crash on unchanged `config/level3.toml`.

This means the next loop should not continue local reward-number, fixed-seed
replay, longer-rollout-only tweaks, or v32 privileged-Critic maturation. It
should move to the next named training-distribution lane: gate-phase reset
curriculum.

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

The immediate executable step is:

```text
v33_gate_phase_reset_curriculum_from_loop097_12m
```

This is a training-only reset curriculum screen. It keeps v5 Actor
observation, loop052 reward/PPO numbers, `256 envs x 128` rollout geometry,
corrected v30 semantics, and hard eval on unchanged `config/level3.toml`.
It changes only the training reset distribution:

- 55% of episodes keep normal Level3 starts;
- 45% of episodes reset near randomized target-gate approach phases;
- the target race track geometry and final hard-eval protocol stay unchanged.

The first screen should train 10M from the loop097/v31d 12M checkpoint and
evaluate 1M/2M/3M/5M/8M/10M milestones on `validation_unseen`.

## Not Yet Implemented

These framework pieces require code support before training:

- separate actor/critic RunningMeanStd if normalization is combined with
  asymmetric Critic later;
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
