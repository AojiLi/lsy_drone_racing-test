# Level3 Gate-Transition Trace Diagnosis

## Scope

This is diagnostic-only. It does not train, tune, or modify Level3 track
geometry/randomization. Acceptance still requires hard eval on
`config/level3_dr.toml`.

Trace CSV: `experiments/level3_ppo_loop/diagnostics/tmp_trace_smoke_trace.csv`

Episode CSV: `experiments/level3_ppo_loop/diagnostics/tmp_trace_smoke_episodes.csv`

Summary JSON: `experiments/level3_ppo_loop/diagnostics/tmp_trace_smoke_summary.json`

## Replay Summary

| Checkpoint | Success | Mean Gates | Crash | Mean Success Time | Endpoint Classes |
| --- | --- | --- | --- | --- | --- |
| level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final | 0.00 | 1.00 | 1.00 | nan | {'gate_side_frame': 1} |

## Conversion And Control Metrics

| Checkpoint | Wrong Side / Ep | Plane Cross / Ep | Center Hit / Ep | Frame Pressure / Ep | Cmd Tilt Over Limit | Action Sat |
| --- | --- | --- | --- | --- | --- | --- |
| level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final | 0.000 | 0.000 | 0.000 | 0.000 | 0.120 | 0.250 |

## Per-Seed Endpoint Summary

| Seed | Checkpoint Outcomes |
| --- | --- |
| 1 | level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m:final: 1g/gate_side_frame/gate_1_left |

## Interpretation

- Use this report to choose between observation, controller/action smoothing,
  curriculum/seed triage, or continued hold.
- Do not treat this diagnostic replay as replacing official hard-eval summary
  CSVs. The hard-eval CSV remains the metric source for best checkpoint and
  target completion.
