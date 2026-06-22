# Level3 Gate-Transition Trace Diagnosis

## Scope

This is diagnostic-only. It does not train, tune, or modify Level3 track
geometry/randomization. Acceptance still requires hard eval on
`config/level3_dr.toml`.

Trace CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_trace.csv`

Episode CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_episodes.csv`

Summary JSON: `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_summary.json`

## Replay Summary

| Checkpoint | Success | Mean Gates | Crash | Mean Success Time | Endpoint Classes |
| --- | --- | --- | --- | --- | --- |
| level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final | 0.20 | 1.40 | 0.80 | 6.975 | {'gate_side_frame': 6, 'near_gate_obstacle': 4, 'success': 4, 'gate_vertical_frame': 2, 'pre_plane_obstacle': 2, 'bounds_or_ground': 1, 'other_crash': 1} |
| level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final | 0.15 | 1.25 | 0.85 | 6.393 | {'gate_side_frame': 6, 'near_gate_obstacle': 6, 'success': 3, 'gate_vertical_frame': 2, 'pre_plane_obstacle': 2, 'other_crash': 1} |
| level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M | 0.10 | 1.25 | 0.90 | 6.400 | {'near_gate_obstacle': 6, 'gate_side_frame': 4, 'pre_plane_obstacle': 4, 'gate_vertical_frame': 2, 'success': 2, 'bounds_or_ground': 1, 'other_crash': 1} |

## Conversion And Control Metrics

| Checkpoint | Wrong Side / Ep | Plane Cross / Ep | Center Hit / Ep | Frame Pressure / Ep | Cmd Tilt Over Limit | Action Sat |
| --- | --- | --- | --- | --- | --- | --- |
| level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.133 | 0.126 |
| level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.180 | 0.132 |
| level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M | 0.000 | 0.000 | 0.000 | 0.000 | 0.104 | 0.121 |

## Per-Seed Endpoint Summary

| Seed | Checkpoint Outcomes |
| --- | --- |
| 1 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 1g/gate_side_frame/gate_1_left ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 1g/gate_side_frame/gate_1_right ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 2g/near_gate_obstacle/obstacle_2 |
| 2 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/near_gate_obstacle/obstacle_0 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 1g/near_gate_obstacle/obstacle_1 |
| 3 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/gate_side_frame/gate_0_right ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/gate_side_frame/gate_0_right ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/near_gate_obstacle/obstacle_0 |
| 4 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 1g/gate_side_frame/gate_3_right ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 1g/near_gate_obstacle/obstacle_2 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 1g/gate_vertical_frame/gate_3_top |
| 5 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 2g/gate_side_frame/gate_2_left ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/gate_side_frame/gate_0_left |
| 6 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 1g/pre_plane_obstacle/obstacle_3 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 1g/near_gate_obstacle/obstacle_1 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 1g/pre_plane_obstacle/obstacle_3 |
| 7 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/gate_vertical_frame/gate_0_bottom ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/gate_side_frame/gate_0_left ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 2g/gate_side_frame/gate_1_right |
| 8 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 3g/near_gate_obstacle/obstacle_3 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 3g/pre_plane_obstacle/obstacle_0 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 3g/pre_plane_obstacle/obstacle_0 |
| 9 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/gate_side_frame/gate_0_right ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/gate_side_frame/gate_0_right ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/gate_side_frame/gate_0_right |
| 10 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 2g/gate_side_frame/gate_1_right ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 2g/gate_side_frame/gate_1_right ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 2g/gate_side_frame/gate_1_right |
| 11 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 4g/success/gate_3_top ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 4g/success/gate_3_left ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 4g/success/gate_3_top |
| 12 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 4g/success/gate_3_left ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 2g/gate_vertical_frame/gate_1_top ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 4g/success/gate_3_left |
| 13 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 4g/success/gate_3_top ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 4g/success/gate_3_top ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 1g/pre_plane_obstacle/obstacle_3 |
| 14 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/other_crash/gate_3_stand ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/other_crash/gate_3_stand ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/other_crash/gate_3_stand |
| 15 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/near_gate_obstacle/obstacle_0 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/near_gate_obstacle/obstacle_0 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/near_gate_obstacle/obstacle_0 |
| 16 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 4g/success/gate_3_bottom ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 4g/success/gate_3_bottom ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 2g/near_gate_obstacle/obstacle_2 |
| 17 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/gate_vertical_frame/gate_0_bottom ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/gate_vertical_frame/gate_0_bottom ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/gate_vertical_frame/gate_0_bottom |
| 18 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/near_gate_obstacle/obstacle_0 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/near_gate_obstacle/obstacle_0 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/near_gate_obstacle/obstacle_0 |
| 19 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 2g/bounds_or_ground/bounds_or_ground ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 2g/near_gate_obstacle/obstacle_1 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 2g/bounds_or_ground/bounds_or_ground |
| 20 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 0g/pre_plane_obstacle/obstacle_1 ; level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m:final: 0g/pre_plane_obstacle/obstacle_1 ; level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m:10M: 0g/pre_plane_obstacle/obstacle_1 |

## Interpretation

- Use this report to choose between observation, controller/action smoothing,
  curriculum/seed triage, or continued hold.
- Do not treat this diagnostic replay as replacing official hard-eval summary
  CSVs. The hard-eval CSV remains the metric source for best checkpoint and
  target completion.
