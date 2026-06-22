# Level3 Gate-Transition Trace Diagnosis

## Scope

This is diagnostic-only. It does not train, tune, or modify Level3 track
geometry/randomization. Acceptance still requires hard eval on
`config/level3_dr.toml`.

Trace CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v25_vs_loop078_v24_trace_diagnostic_trace.csv`

Episode CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v25_vs_loop078_v24_trace_diagnostic_episodes.csv`

Summary JSON: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v25_vs_loop078_v24_trace_diagnostic_summary.json`

## Replay Summary

| Checkpoint | Success | Mean Gates | Crash | Mean Success Time | Endpoint Classes |
| --- | --- | --- | --- | --- | --- |
| level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final | 0.25 | 2.05 | 0.75 | 8.048 | {'gate_side_frame': 6, 'near_gate_obstacle': 6, 'success': 5, 'pre_plane_obstacle': 3} |
| level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final | 0.15 | 1.45 | 0.85 | 7.173 | {'gate_side_frame': 6, 'near_gate_obstacle': 5, 'gate_vertical_frame': 4, 'success': 3, 'pre_plane_obstacle': 2} |
| level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M | 0.10 | 1.35 | 0.90 | 7.250 | {'gate_side_frame': 7, 'pre_plane_obstacle': 6, 'near_gate_obstacle': 3, 'gate_vertical_frame': 2, 'success': 2} |

## Conversion And Control Metrics

| Checkpoint | Wrong Side / Ep | Plane Cross / Ep | Center Hit / Ep | Frame Pressure / Ep | Cmd Tilt Over Limit | Action Sat |
| --- | --- | --- | --- | --- | --- | --- |
| level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.081 |
| level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.062 |
| level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M | 0.000 | 0.000 | 0.000 | 0.000 | 0.018 | 0.061 |

## Per-Seed Endpoint Summary

| Seed | Checkpoint Outcomes |
| --- | --- |
| 1 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 3g/pre_plane_obstacle/obstacle_3 |
| 2 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 0g/gate_side_frame/gate_0_left |
| 3 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/near_gate_obstacle/obstacle_1 |
| 4 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_right ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 4g/success/gate_3_right ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/gate_vertical_frame/gate_0_top |
| 5 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/near_gate_obstacle/obstacle_1 |
| 6 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_3_right ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 2g/gate_vertical_frame/gate_3_bottom ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 2g/gate_side_frame/gate_3_right |
| 7 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 0g/pre_plane_obstacle/obstacle_1 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 0g/pre_plane_obstacle/obstacle_1 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 0g/pre_plane_obstacle/obstacle_1 |
| 8 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 3g/gate_side_frame/gate_3_right ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 4g/success/gate_3_bottom ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 4g/success/gate_3_bottom |
| 9 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_right ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 4g/success/gate_3_bottom ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 4g/success/gate_3_right |
| 10 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_left ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/gate_side_frame/gate_0_right |
| 11 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/near_gate_obstacle/obstacle_2 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 2g/near_gate_obstacle/obstacle_2 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 2g/near_gate_obstacle/obstacle_2 |
| 12 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_top ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 2g/gate_side_frame/gate_1_right ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 0g/gate_vertical_frame/gate_0_top |
| 13 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/near_gate_obstacle/obstacle_2 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 0g/gate_side_frame/gate_0_left |
| 14 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 0g/gate_side_frame/gate_0_right ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 0g/gate_side_frame/gate_0_right |
| 15 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_right ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 2g/gate_side_frame/gate_2_right ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/pre_plane_obstacle/obstacle_0 |
| 16 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/pre_plane_obstacle/obstacle_3 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/pre_plane_obstacle/obstacle_3 ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/pre_plane_obstacle/obstacle_3 |
| 17 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 2g/gate_side_frame/gate_1_left ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/gate_vertical_frame/gate_0_top ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 2g/gate_side_frame/gate_1_left |
| 18 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_left ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 2g/gate_vertical_frame/gate_1_bottom ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 2g/gate_side_frame/gate_1_left |
| 19 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 4g/success/gate_3_bottom ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 0g/gate_vertical_frame/gate_0_bottom ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/pre_plane_obstacle/obstacle_1 |
| 20 | level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m:final: 1g/pre_plane_obstacle/obstacle_0 ; level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m:final: 1g/gate_side_frame/gate_0_right ; level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m:5M: 1g/pre_plane_obstacle/obstacle_0 |

## Interpretation

- Use this report to choose between observation, controller/action smoothing,
  curriculum/seed triage, or continued hold.
- Do not treat this diagnostic replay as replacing official hard-eval summary
  CSVs. The hard-eval CSV remains the metric source for best checkpoint and
  target completion.
