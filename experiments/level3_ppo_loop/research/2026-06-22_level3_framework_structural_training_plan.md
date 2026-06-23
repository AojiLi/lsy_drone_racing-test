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
`1.41` mean gates, and `86%` crash. loop107 tested residual-GRU transfer from
loop101; its 1M checkpoint reached the current corrected-loop success best at
`21/100`, `1.66` mean gates, and `79%` crash, but later checkpoints drifted
down to `15/100`, `12/100`, `12/100`, and `17/100`. loop108 then tested a
short continuation from loop107 1M and failed to reproduce it: best was only
`18/100`, `1.58` mean gates, and `82%` crash.

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
v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m
```

loop110/v39 tied the current success/crash frontier at its 3M checkpoint with
21% success, 1.64 mean gates, 79% crash, and 6.756s mean successful time. It
also solved 8 validation seeds not solved by loop107 1M, but later checkpoints
regressed and mean gates did not beat the loop101/loop107 frontier. The next
runnable step is a bounded same-hypothesis continuation from loop110 3M,
approved by
`experiments/level3_ppo_loop/decisions/2026-06-23_loop110_continue_v39b_from_3m.md`.
It must keep unchanged `config/level3.toml`, v5 Actor observation, MLP policy,
v39 reward numbers, and Actor-only deployment. Do not start this lane from
loop110 final.

## Not Yet Implemented

These framework pieces require code support before training:

- separate actor/critic RunningMeanStd if normalization is combined with
  asymmetric Critic later;
- tanh-squashed Gaussian PPO log-prob parity;
- sequence-level teacher-success retention datasets for residual-GRU students,
  if online current-minibatch retention is not enough.

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
