# Decision: V56 Task 4 Passed Semantics, Launch Task 3 Near-Plane Backout

## Decision

Continue the v56 geometric planner loop with exactly one next planner knob:

```text
v56_task3_near_plane_backout
```

The goal is to stop hard-cross attempts when the drone is near the gate plane
but clearly outside the aperture corridor.

## Evidence

Task 4 fixed the hard semantic guard:

- `recover_before_gate_switch_count = 0`
- `fake_recover_count = 0`
- phase 5 rows: `0`
- real target-gate switches only occurred on seeds `113` and `120`

But v56 performance still failed:

- gate0 pass: `2/20`
- first-gate progress: `19/20`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml` unchanged

The trace reviewer found the remaining high-value failure buckets:

- contact near gate without pass: `103, 104, 108, 110, 112, 116`
- cross-phase contact without pass:
  `101, 102, 106, 109, 111, 115, 117, 119`

The next-hypothesis reviewer recommended Task 3. The main agent agrees because
the dominant residual failure is not just speed; it is crossing or staying in
cross while Y/Z is too far from the aperture corridor.

## Task 3 Scope

Implement one strategy knob:

```text
if same environment target_gate is still active
and abs(gate_local_x) < 0.35
and aperture-relative Y/Z error > 0.30:
    force or keep phase = align
    reference the pre-gate align point
```

Do not change:

- cross speed;
- Task 1 thresholds;
- PPO or tracker checkpoint;
- reward;
- observation layout;
- MPPI or planner action output;
- `config/level3.toml`.

## Acceptance For Task 3

Task 3 local gate:

- `large_yz_cross_attempt_count <= 2/20`
- `contact_count <= 10/20`
- `gate0_pass_count >= 3/20`

Preserve Task 4 guard:

- `recover_before_gate_switch_count = 0`
- `fake_recover_count = 0`
- only environment `target_gate` transition counts as gate pass

Full v56 target remains:

- first-gate progress `20/20`
- gate0 pass `>=10/20`
- contact `<=8/20`
- early termination `<=6/20`
- all finite
- unchanged `config/level3.toml`

## Next Smoke Command

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 500 \
  --early-termination-step-threshold 50 \
  --trace-output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task3_near_plane_backout_500step_trace.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task3_near_plane_backout_500step_metrics.json
```
