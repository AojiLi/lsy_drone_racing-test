# v55 Decision: Hold Long Training, Tune Geometric Planner First

## Decision

`manual_long_level3_training_review` is not approved for a long PPO or
planner-tracker training run yet.

Next action:

```text
launch_tracker_structural_fix: planner-only GeometricSlowGatePlanner tuning
```

The fix must keep `config/level3.toml` unchanged and keep the PPO tracker as
the only action source. The upper planner may only output reference points,
desired speed, and desired heading.

## Evidence

The 500-step planner smoke on seeds `101-120` passed the formal stage gate:

```text
nonzero_first_gate_progress_ratio = 1.0
gate0_pass_count = 3
early_termination_ratio = 0.1
all_finite = true
checkpoint_backed = true
level3_toml_diff_clean = true
```

However, this is still far from reliable Level3 completion. The trace diagnostic
shows:

```text
termination_reasons = {"contact": 15, "max_steps": 5}
passed_gate0_then_contact_later = 3
contact_before_gate_plane = 7
contact_near_gate_without_pass = 3
crossed_plane_far_outside_aperture_timeout = 5
immediate_or_early_contact = 2
```

Successful gate0 passes crossed near the aperture center (`YZ error ~=0.10m` to
`0.19m`). Failed plane crossings were usually far outside the aperture
(`YZ error ~=0.5m+`).

## Rationale

The loop is alive: every seed makes first-gate progress, and longer horizon
increased gate0 passes from `1/20` to `3/20`.

The blocker is now aperture geometry and contact avoidance, not evidence that a
long PPO run should start. A long run would mostly measure the same unsafe
planner references. The cleaner next move is to make the deterministic planner
more conservative:

- align longer before crossing;
- reduce cross speed;
- handle near-plane/off-aperture initial states by backing out to pre-gate;
- prevent recover phase before an actual target-gate switch;
- rerun the same 500-step trace smoke.

## Required Checks For The Next Fix

Before approving any training command, run:

```bash
pixi run -e tests pytest tests/unit/scripts/test_level3_tracker_stage_evaluator.py -q
pixi run -e tests ruff check scripts/check_level3_reference_tracker_smoke.py scripts/evaluate_level3_tracker_stage.py lsy_drone_racing/control/level3_reference_tracker_controller.py lsy_drone_racing/control/level3_reference_tracker.py
git diff -- config/level3.toml
```

Then rerun:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 500 \
  --early-termination-step-threshold 50 \
  --trace-output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_geometric_slow_gate_planner_smoke_101_120_500step_trace.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_geometric_slow_gate_planner_smoke_101_120_500step_metrics.json
```

Target for the next planner-only smoke:

```text
gate0_pass_count > 3
contact_before_gate_plane decreases
near-plane failed crossings have lower Y/Z error
no config/level3.toml changes
```
