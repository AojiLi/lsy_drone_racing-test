# Loop077 V21 Trace Diagnostic Synthesis

Scope: diagnostic synthesis after rejecting loop077/v21. This does not train,
tune, or modify `config/level3_dr.toml`. Hard acceptance remains success rate
`>= 0.60` and mean successful time `<= 7.0s` on the unchanged Level3 hard
evaluator.

Inputs:

- Loop077 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.md`
- Loop077 decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop077_reject_v21_hold_for_trace_diagnostics.md`
- Trace report:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop069_071_076_077_v21_trace_diagnostic_report.md`
- Trace episodes:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop069_071_076_077_v21_trace_diagnostic_episodes.csv`

## Summary

The v21 gate-acquisition reward increase is rejected. It did not convert into
more hard-eval success. It narrowed the success set and increased obstacle/frame
crashes.

| Checkpoint | Success | Success Seeds | Mean Gates | Crash | Main Endpoint Pattern |
| --- | ---: | --- | ---: | ---: | --- |
| loop069 25M | 0.10 | 4, 9 | 1.45 | 0.90 | mixed frame/obstacle |
| loop071 20M | 0.25 | 4, 5, 8, 9, 12 | 2.00 | 0.75 | best frontier |
| loop076 5M | 0.20 | 8, 9, 12, 18 | 1.65 | 0.80 | loses 4/5, keeps 8/9/12 |
| loop077 5M | 0.10 | 3, 4 | 1.70 | 0.90 | near-gate obstacle rises |
| loop077 10M | 0.10 | 4, 9 | 1.50 | 0.90 | frame crashes rise |
| loop077 15M | 0.10 | 4, 9 | 1.55 | 0.90 | obstacle/frame mix |
| loop077 final | 0.05 | 9 | 1.35 | 0.95 | vertical-frame rise |

The diagnostic-only union of recent checkpoint successes is seeds
`[3, 4, 5, 8, 9, 12, 18]`, or 35% on this fixed 20-seed set. That is not a
deployable result because it assumes checkpoint selection knowledge, but it
proves the checkpoint families contain complementary behavior.

## Interpretation

- Loop071 remains the best diagnostic frontier.
- Loop076 default recovery preserved some non-replay transfer but lost seed 4
  and seed 5 from loop071.
- Loop077/v21 restored seed 4 at some milestones but destroyed key loop071
  successes on seeds 5, 8, and 12.
- The stronger gate reward increased training reward/gate reward but did not
  increase real passed-gate conversion.
- The dominant failures are not measured as wrong-side or plane-cross events in
  this trace script. They occur as near-gate obstacle and gate-frame crashes.
- Later v21 checkpoints show higher command-tilt-over-limit fractions than
  loop071 and no success-rate gain.

## Rejected Directions

Do not continue or mature:

- v19 seed replay
- v20 default-distribution recovery
- v21 strong gate-acquisition reward numbers

Do not rerun the analyzer's same reward-number recommendation. It already
failed in loop077.

Do not naively continue loop069 or loop071. Those continuations were already
rejected by loop070 and loop072.

## Next Candidate Direction

The next useful lane should be structural, not another simple reward-number
increase. The strongest candidate is an observation/geometry lane from the
loop071 20M frontier:

`v22_loop071_gate_corridor_obstacle_obs_default_20m`

Rationale:

- The recurring failure is near-gate obstacle/frame collision.
- Reward pressure alone made that worse.
- Seed replay made transfer worse.
- The existing codebase supports a gate-corridor obstacle observation layout
  and zero-padding warm-start from local-obstacle checkpoints.
- The prior v8 gate-corridor observation test started from loop052, not from
  the stronger loop071 frontier. Retesting this structure from loop071 is a
  different hypothesis.

Initial v22 contract if launched:

- start from loop071 20M
- train on `level3_dr.toml`
- hard eval on unchanged `level3_dr.toml`
- use `level3_gate_corridor_obstacle_relative_obs_v8`-style layout already
  supported by the repo
- keep reward numbers, PPO settings, controller settings, and default
  distribution fixed initially
- use a 20M screen with 5M checkpoint evaluation

Before launching v22, write an explicit decision packet and dry-run the
registered lane.
