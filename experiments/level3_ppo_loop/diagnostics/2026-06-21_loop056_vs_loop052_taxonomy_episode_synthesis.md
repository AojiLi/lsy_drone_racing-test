# Loop056 vs Loop052 Taxonomy And Episode Synthesis

Date: 2026-06-21

## Scope

- Target remains hard eval on `config/level3_dr.toml`.
- Level3 track geometry and randomization were not modified.
- This packet compares the current global best loop052 against loop056 before
  any further training decision.

## Hard-Eval Summary

Current global best remains loop052 final:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Hard evaluator, seeds 1-20:

- Success: `0.20`
- Crash: `0.80`
- Mean gates: `1.40`
- Mean successful time: `6.975s`

Loop056 best was the 5M checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m_step_005000000.ckpt`

Hard evaluator, seeds 1-20:

- Success: `0.15`
- Crash: `0.85`
- Mean gates: `1.20`
- Mean successful time: `6.96s`

Loop056 final:

- Success: `0.10`
- Crash: `0.90`
- Mean gates: `1.35`

Interpretation: loop056 did not improve the frontier. It recovered some final
gate count but lost successful completions and crash rate.

## Episode-Level Comparison

Hard-eval episode CSV comparison, loop052 final versus loop056 5M:

- Gate count improved on `2 / 20` seeds.
- Gate count worsened on `3 / 20` seeds.
- Gate count stayed the same on `15 / 20` seeds.
- loop052 final success seeds: `11, 12, 13, 16`.
- loop056 5M success seeds: `8, 11, 16`.

Changed seeds:

- seed `6`: loop052 `1` gate crash -> loop056 `2` gates crash
- seed `8`: loop052 `3` gates crash -> loop056 success
- seed `12`: loop052 success -> loop056 `2` gates crash
- seed `13`: loop052 success -> loop056 `1` gate crash
- seed `19`: loop052 `2` gates crash -> loop056 `1` gate crash

Interpretation: loop056 mostly reshuffled seed outcomes. It did not produce a
stable cross-seed improvement.

## Crash Taxonomy

Crash taxonomy artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_052_final_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_052_final_20seed_crash_taxonomy_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_056_5M_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_056_5M_20seed_crash_taxonomy_episodes.csv`

Note: the taxonomy tool uses a single-controller replay path and differs from
the hard evaluator on individual seeds, so it is diagnostic only. The hard
evaluator remains the acceptance gate.

Taxonomy loop052 final:

- Successes: `3 / 20`
- Crashes: `17 / 20`
- Crash target gates: gate0 `9`, gate1 `2`, gate2 `5`, gate3 `1`
- Top likely objects: `obstacle_0` `4`, `gate_0_bottom` `2`,
  `gate_0_right` `2`, `obstacle_1` `2`, `obstacle_2` `2`

Taxonomy loop056 5M:

- Successes: `3 / 20`
- Crashes: `17 / 20`
- Crash target gates: gate0 `9`, gate1 `5`, gate2 `3`
- Top likely objects: `obstacle_1` `3`, `gate_0_bottom` `2`,
  `gate_0_right` `2`, `obstacle_0` `2`

Interpretation:

- Both policies still mostly fail at early gates and nearby obstacles.
- loop056 shifted some crashes from gate2/gate3 back toward gate1.
- The light soft-centerline plane reward did not reduce the early crash
  structure.

## Parameter Evidence

The analyzer's gate-acquisition recommendation after loop056 matches the
already-tested loop051 aggressive gate-acquisition direction:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- `time_penalty=0.02`

Loop051 result:

- Success: `0.10`
- Crash: `0.90`
- Mean gates: `1.15`

Loop054 already tested a milder gate-pressure move from loop052:

- Success: `0.15`
- Crash: `0.85`
- Mean gates: `1.20`

Interpretation: immediately launching the analyzer's gate-acquisition command
would repeat failed local evidence rather than test a new hypothesis.

## Conclusion

Do not continue loop056.

Do not launch the analyzer's aggressive gate-acquisition reward command without
a new reason that distinguishes it from loop051.

The next useful work should be analysis or research to define a genuinely new
structural hypothesis for early-gate survival/pass conversion, with the Level3
track unchanged and loop052 final retained as the current global-best fallback.

