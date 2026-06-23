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

loop101 then tested the gate-phase reset curriculum from loop097 for 10M. It
tied the old success frontier at `20/100`, improved mean gates slightly to
`1.69`, and improved mean successful time to `6.873s`, but crash remained
`80/100`. Its 8M checkpoint reached `1.81` mean gates with only `19/100`
success. This means v33 is not a breakthrough and should not continue as-is.
loop102 tested the next named training-distribution lane, low-probability
offline train-pool PLR, and it regressed validation-unseen hard eval. The next
loop returned to loop101 final and tested competence-gated gate-phase reset
curriculum. loop103 did not beat the loop101 frontier: best was `19/100`,
`1.68` mean gates, and `81%` crash, and the competence gate never opened.
loop106 then tested online competence-gated level replay from loop101 and also
failed to improve the frontier: its best checkpoint tied `20/100` success but
fell to `1.63` mean gates and `7.744s`, while final collapsed to `14/100`,
`1.41` mean gates, and `86%` crash. The next lane should reject replay tuning
and move to a GRU transfer / memory-structure preflight from loop101.

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

## Immediate Lane

The immediate step is:

```text
v37_gru_transfer_memory_structure_from_loop101
```

This is now a bounded 5M screening command. It keeps v5 Actor observation,
loop052 reward/PPO numbers, corrected v30 semantics, default random track
generation, and hard eval on unchanged `config/level3.toml`, but changes the
Actor structure to `mlp_residual_recurrent_actor_gru256`. Because the old
from-scratch GRU lane failed, the implementation preserves loop101's MLP
Actor/Critic exactly and adds a zero-initialized GRU residual branch. The
support/preflight gate passed in
`experiments/level3_ppo_loop/parity/2026-06-23_v37_residual_gru_transfer_preflight.md`.

## Not Yet Implemented

These framework pieces require code support before training:

- separate actor/critic RunningMeanStd if normalization is combined with
  asymmetric Critic later;
- tanh-squashed Gaussian PPO log-prob parity;
- broader GRU distillation or memory pretraining if v37 residual-GRU transfer
  fails to convert loop101 parity into evaluator progress.

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
