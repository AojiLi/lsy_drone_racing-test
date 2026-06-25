# v55 Line Tracking Attempt001 Terminal-Hold Re-Eval

Date: 2026-06-25

Stage: `line_tracking`

Checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_from_brake_attempt001_final.ckpt
```

## Result

After the terminal-hold semantic fix, the existing checkpoint improved
substantially but still did not pass the line-tracking gate.

| Metric | Required | Re-eval |
|---|---:|---:|
| `success_rate` | `>= 0.90` | `1.0` |
| `crash_rate` | `<= 0.05` | `0.0` |
| `mean_cross_track_error_m` | `<= 0.12` | `0.08466855436563492` |
| `p90_cross_track_error_m` | `<= 0.22` | `0.22865745425224304` |
| `mean_speed_error_mps` | `<= 0.18` | `0.06138031929731369` |
| `mean_action_delta_l2` | `<= 0.28` | `0.01066624652594328` |

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_line_tracking_from_brake_attempt001_final_terminal_hold_metrics.json
```

## Interpretation

The semantic fix solved the speed-error failure:

```text
old mean_speed_error_mps = 0.3112734258174896
new mean_speed_error_mps = 0.06138031929731369
```

The remaining failure is narrow:

```text
p90_cross_track_error_m = 0.22865745425224304
threshold = 0.22
gap = 0.00865745425224304m
```

The stage should stay on `line_tracking`. The next attempt should fine-tune the
same checkpoint under the corrected terminal-hold semantics with modestly
stronger position/progress pressure, while preserving the already-passing
speed, crash, and action-smoothness metrics.
