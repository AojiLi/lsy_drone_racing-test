# Decision: Launch V52 MPPI Oracle Teacher Loop

Decision: `launch_named_structural_lane`

Approved lane:

```text
v52_mppi_oracle_teacher_level3
```

Research packet:
`experiments/level3_ppo_loop/research/2026-06-25_level3_v52_mppi_oracle_teacher_plan.md`

Superseded hold:
`experiments/level3_ppo_loop/decisions/2026-06-25_loop122_hold_for_v51_planner_diagnostics.md`

## Decision

Launch a new MPPI oracle/teacher loop before any further PPO training.

The current v51 planner-guidance observation result did not improve the PPO
frontier. The user has now explicitly approved testing MPPI as a stronger
controller/teacher route, while keeping `config/level3.toml` immutable.

## Rationale

Current PPO hard-eval frontier:

- success: `21%`;
- mean gates: `1.66`;
- crash: `79%`;
- mean successful time: `7.578s`;
- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`.

Recent structural PPO lanes, including hidden512, update-pressure repair,
retention, reward-structure changes, and planner-guidance observation, did not
move the frontier toward the `60%` target. v51 in particular showed that giving
PPO route-intent hints as observation is weaker than having an oracle/controller
that can actively search action sequences.

MPPI should therefore be tested as an oracle:

```text
Level3 observation
-> MPPI action-sequence sampling and scoring
-> roll / pitch / yaw / thrust
-> hard eval on unchanged config/level3.toml
```

This MPPI result must not be recorded as PPO success. It is an oracle/controller
diagnostic and potential teacher-data source.

## Approved Scope

Approved:

- implement `v52_mppi_oracle_teacher_level3`;
- add an MPPI controller module that may output actions during MPPI oracle eval;
- add or adapt an evaluator for non-PPO controllers;
- run smoke evals and then hard eval on unchanged `config/level3.toml`;
- if MPPI is strong enough, generate successful trajectory/action data for PPO
  BC/DAgger/fine-tuning in a later named lane.

Not approved:

- editing `config/level3.toml` geometry, gates, obstacles, randomization, or
  validation seed split;
- launching PPO training before MPPI analysis justifies teacher data;
- treating MPPI-only success as PPO target success;
- static seed-specific route replay;
- inference-time safety shields or fallback rule controllers inside PPO lanes
  without a later packet.

## Required Builder/Checker Gate

Before any MPPI eval, run the builder/checker gate because this touches
controller action output and evaluator semantics.

Builder must implement the smallest useful MPPI oracle loop support:

1. A Level3 MPPI controller module, likely
   `lsy_drone_racing/control/mppi_level3_oracle.py`.
2. A generic Level3 controller evaluator or an evaluator extension that does
   not require PPO checkpoints.
3. Smoke commands for a tiny seed set.
4. Full validation command shape for `validation_unseen 101-200`.
5. Dataset-generation support only behind an explicit post-MPPI evidence gate,
   or a clear follow-up implementation packet if dataset support is deferred.

Checker must verify:

- `git diff --check`;
- Python compile checks for touched scripts/modules;
- evaluator dry-run or tiny smoke eval;
- `config/level3.toml` unchanged;
- MPPI controller returns finite `[roll, pitch, yaw, thrust]` actions;
- result files are small source/analysis outputs only, with datasets/logs
  ignored unless explicitly requested.

## Evaluation Protocol

Stage A: smoke

- 5-10 seeds;
- verify finite actions, no NaNs, no evaluator crash, and sane termination
  logging.

Stage B: dev hard eval

- small non-final seed set;
- compare mean gates and crash against current PPO behavior.

Stage C: validation hard eval

- validation split: `validation_unseen 101-200`;
- config: `config/level3.toml`;
- success gate: `>=60%`;
- time gate: `<=7.0s` mean successful time.

## Promotion Rules

- If MPPI reaches `>=60%` success and `<=7.0s`, treat it as a viable Level3
  controller candidate and a high-value PPO teacher.
- If MPPI reaches `>=40%` success or clearly expands the solved-seed set beyond
  PPO, generate successful demonstration data in a follow-up named lane.
- If MPPI remains near the PPO plateau, continue MPPI cost/model/horizon work
  before PPO imitation.
- If MPPI is unstable or too slow for runtime use but can produce offline
  successes, keep it as an offline teacher only.

## Next Action

Do not start PPO training.

Next executable work is implementation/preflight for
`v52_mppi_oracle_teacher_level3` through the builder/checker gate.
