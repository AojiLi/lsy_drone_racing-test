# v55 Tracker Decision: Continue Line Tracking With Position Fine-Tune

Date: 2026-06-25

Decision: `change_tracker_reward_numbers`

Stage:

```text
line_tracking
```

## Decision

Do not unlock `heading_tracking` yet.

Launch `line_tracking` attempt002 from the attempt001 final checkpoint under
the corrected terminal-hold semantics. Use a short, bounded fine-tune focused
on reducing p90 cross-track error.

Approved initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_from_brake_attempt001_final.ckpt
```

Approved changes:

```text
pos_error_coef: 3.0 -> 4.0
progress_bonus: 0.3 -> 0.45
total_timesteps: 2M
checkpoint_interval: 500k
```

Keep:

```text
vel_error_coef = 0.6
1024 envs x 32 steps
hidden_dim = 256
learning_rate = 3e-4
```

## Why

After terminal-hold re-evaluation, speed error is now safely passing:

```text
mean_speed_error_mps = 0.06138031929731369 <= 0.18
```

The only remaining failure is p90 cross-track error, narrowly above threshold:

```text
p90_cross_track_error_m = 0.22865745425224304 > 0.22
```

This is a small tracking-accuracy miss, not a crash/safety issue and not an
obvious PPO instability issue.

## Next Action

Run:

```text
v55_tracker_line_tracking_terminal_hold_position_attempt002
```

Evaluate `500k`, `1M`, `1.5M`, and final checkpoints. Use the corrected
terminal-hold evaluator. Only unlock `heading_tracking` if the official
`line_tracking` gate checker passes with prerequisite history.
