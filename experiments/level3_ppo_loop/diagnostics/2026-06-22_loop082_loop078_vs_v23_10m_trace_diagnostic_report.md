# Level3 Gate-Transition Trace Diagnosis

## Scope

This is diagnostic-only. It does not train, tune, or modify Level3 track
geometry/randomization. Acceptance still requires hard eval on
`config/level3_dr.toml`.

Trace CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_loop078_vs_v23_10m_trace_diagnostic_trace.csv`

Episode CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_loop078_vs_v23_10m_trace_diagnostic_episodes.csv`

Summary JSON: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_loop078_vs_v23_10m_trace_diagnostic_summary.json`

## Replay Summary

| Checkpoint | Success | Mean Gates | Crash | Mean Success Time | Endpoint Classes |
| --- | --- | --- | --- | --- | --- |
| level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final | 0.25 | 2.05 | 0.75 | 8.048 | {'gate_side_frame': 6, 'near_gate_obstacle': 6, 'success': 5, 'pre_plane_obstacle': 3} |
| level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M | 0.20 | 2.00 | 0.80 | 8.855 | {'near_gate_obstacle': 7, 'gate_side_frame': 4, 'success': 4, 'gate_vertical_frame': 2, 'pre_plane_obstacle': 2, 'bounds_or_ground': 1} |

## Conversion And Control Metrics

| Checkpoint | Wrong Side / Ep | Plane Cross / Ep | Center Hit / Ep | Frame Pressure / Ep | Cmd Tilt Over Limit | Action Sat |
| --- | --- | --- | --- | --- | --- | --- |
| level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.081 |
| level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M | 0.000 | 0.000 | 0.000 | 0.000 | 0.020 | 0.082 |

## Per-Seed Endpoint Summary

| Seed | Checkpoint Outcomes |
| --- | --- |
| 1 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/near_gate_obstacle/obstacle_1 |
| 2 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 0g/gate_side_frame/gate_0_left |
| 3 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/near_gate_obstacle/obstacle_1 |
| 4 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_right ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 4g/success/gate_3_right |
| 5 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 4g/success/gate_3_top |
| 6 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_3_right ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 2g/gate_vertical_frame/gate_3_bottom |
| 7 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 0g/pre_plane_obstacle/obstacle_1 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 0g/pre_plane_obstacle/obstacle_1 |
| 8 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 3g/gate_side_frame/gate_3_right ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 3g/gate_side_frame/gate_3_right |
| 9 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_right ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/gate_side_frame/gate_1_right |
| 10 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_left ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/near_gate_obstacle/obstacle_1 |
| 11 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/near_gate_obstacle/obstacle_2 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 2g/near_gate_obstacle/obstacle_2 |
| 12 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_top ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 4g/success/gate_3_left |
| 13 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/near_gate_obstacle/obstacle_2 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/bounds_or_ground/bounds_or_ground |
| 14 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/near_gate_obstacle/obstacle_1 |
| 15 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_right ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 2g/gate_vertical_frame/gate_1_top |
| 16 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/pre_plane_obstacle/obstacle_3 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 1g/pre_plane_obstacle/obstacle_3 |
| 17 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_left ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 2g/gate_side_frame/gate_1_left |
| 18 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_left ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 4g/success/gate_3_bottom |
| 19 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_bottom ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 3g/near_gate_obstacle/obstacle_3 |
| 20 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/pre_plane_obstacle/obstacle_0 ; level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m:10M: 3g/near_gate_obstacle/obstacle_3 |

## Interpretation

- Use this report to choose between observation, controller/action smoothing,
  curriculum/seed triage, or continued hold.
- Do not treat this diagnostic replay as replacing official hard-eval summary
  CSVs. The hard-eval CSV remains the metric source for best checkpoint and
  target completion.
