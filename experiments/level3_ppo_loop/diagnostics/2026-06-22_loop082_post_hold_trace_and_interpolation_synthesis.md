# Loop082 Post-Hold Trace And Interpolation Synthesis

Scope: diagnostic-only synthesis after rejecting loop082/v25. This does not
train, tune, or modify `config/level3_dr.toml`. Hard acceptance remains
success rate `>= 0.60` and mean successful time `<= 7.0s` on unchanged
`config/level3_dr.toml`.

## Inputs

- Main decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop082_reject_v25_hold_for_trace_diagnostics.md`
- Loop082 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.md`
- V25 vs loop078/v24 trace diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v25_vs_loop078_v24_trace_diagnostic_report.md`
- Loop078 vs v23 10M trace diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_loop078_vs_v23_10m_trace_diagnostic_report.md`
- Loop078/v23 10M weight interpolation eval:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop083_loop078_v23_10m_weight_interpolation_eval_summary.csv`

## Current Frontier

The global best remains loop078 final:

- success: 0.25
- mean gates: 2.05
- crash: 0.75
- mean successful time: 8.048s
- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_final.ckpt`

V25 is rejected:

- best success: 0.10
- mean gates: 1.35
- crash: 0.90
- mean successful time: 7.25s

## Seed Retention

Loop078 successful seeds:

- 4, 9, 12, 18, 19

V24 successful seeds:

- 4, 8, 9

V25 successful seeds:

- 8, 9

V23 10M successful seeds:

- 4, 5, 12, 18

Interpretation:

- Aperture observation additions did not produce additive skill.
- V24/V25 gained or retained seed 8 but lost multiple loop078 successes,
  especially 12, 18, and 19.
- V23 10M is closer to loop078 retention than v24/v25 and adds seed 5, but it
  loses seed 9 and 19.
- The union across these checkpoints is still only 7/20 seeds, well below the
  12/20 target.

## Failure-Mode Shift

Loop078 endpoint classes:

- gate side frame: 6
- near-gate obstacle: 6
- pre-plane obstacle: 3
- success: 5

V24 endpoint classes:

- gate side frame: 6
- near-gate obstacle: 5
- gate vertical frame: 4
- pre-plane obstacle: 2
- success: 3

V25 endpoint classes:

- gate side frame: 7
- pre-plane obstacle: 6
- near-gate obstacle: 3
- gate vertical frame: 2
- success: 2

Interpretation:

- V24/V25 do not reduce the dominant hard-eval failure classes enough.
- V25 shifts failures toward pre-plane obstacle and early gate-frame failures.
- This supports rejecting further aperture-layout additions from loop078 without
  a stronger source-backed reason.

## Interpolation Diagnostic

Simple interpolation between loop078 final and v23 10M did not improve the
frontier:

- alpha 0.25: 0.20 success, 2.00 mean gates, 0.80 crash, 7.695s
- alpha 0.50: 0.15 success, 1.90 mean gates, 0.85 crash, 8.020s
- alpha 0.75: 0.15 success, 1.90 mean gates, 0.85 crash, 8.667s

Interpretation:

- The loop078/v23 complement cannot be recovered by naive weight averaging.
- Do not use interpolated checkpoints as the next best model.

## Recommendation

Hold before v26. The next training lane should not be another aperture
observation append, hidden512 run, GRU screen, or naive loop078/v23
interpolation.

A next lane needs a new explicit packet that explains how it will preserve
loop078's successful seeds while improving the dominant failures:

- gate side frame
- near-gate obstacle
- pre-plane obstacle

Until that packet exists, keep the production/best controller as loop078 final.

Do not modify Level3 track geometry, randomization, gates, or obstacles.
