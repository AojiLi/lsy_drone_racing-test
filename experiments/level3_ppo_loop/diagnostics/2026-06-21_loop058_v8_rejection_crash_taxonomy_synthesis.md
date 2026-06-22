# Loop058 V8 Rejection Crash Taxonomy Synthesis

Date: 2026-06-21

## Scope

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry and randomization were not modified.
- Taxonomy replay is diagnostic only; hard-eval CSV remains the acceptance
  source.

## Compared Checkpoints

Loop052 global best:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Loop057 v8 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_step_025000000.ckpt`

Loop058 v8 final:

`lsy_drone_racing/control/checkpoints/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m_final.ckpt`

## Hard Eval Summary

Loop052 final:

- Success: `0.20`
- Crash: `0.80`
- Mean gates: `1.40`
- Mean successful time: `6.975s`

Loop057 v8 25M:

- Success: `0.15`
- Crash: `0.85`
- Mean gates: `1.40`
- Mean successful time: `6.153333333333333s`

Loop058 v8 final:

- Success: `0.15`
- Crash: `0.85`
- Mean gates: `1.20`
- Mean successful time: `6.986666666666667s`

## Taxonomy Summary

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_052_final_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_057_25M_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_058_final_20seed_crash_taxonomy_summary.json`

Loop052 final diagnostic replay:

- Successes: `3 / 20`
- Crashes: `17 / 20`
- Crash target gates: gate0 `9`, gate1 `2`, gate2 `5`, gate3 `1`
- Top likely objects: obstacle0 `4`, gate0 bottom/right `4`, obstacles1/2 `4`

Loop057 v8 25M diagnostic replay:

- Successes: `4 / 20`
- Crashes: `16 / 20`
- Crash target gates: gate0 `7`, gate1 `6`, gate2 `3`
- Top likely objects: obstacle0 `4`, gate0 right `3`, obstacle1 `2`

Loop058 v8 final diagnostic replay:

- Successes: `2 / 20`
- Crashes: `18 / 20`
- Crash target gates: gate0 `9`, gate1 `4`, gate2 `5`
- Top likely objects: obstacle0/1/2 each `3`, plus gate-frame hits.

Seed-level gate comparison, loop057 25M versus loop058 final:

- improved on `2 / 20` seeds;
- worsened on `5 / 20` seeds;
- unchanged on `13 / 20` seeds.

## Interpretation

The v8 maturation lost the weak diagnostic benefit seen in loop057. Failures
returned to the same early-gate distribution as loop052, with no reduction in
gate0 or obstacle crashes. This supports rejecting v8 continuation.

The dominant failure is still early gate/obstacle pass-conversion. The next
experiment should not be framed as speed optimization. It should either refine
the loop052 policy neighborhood or make a larger, explicitly named controller
or training-structure change.
