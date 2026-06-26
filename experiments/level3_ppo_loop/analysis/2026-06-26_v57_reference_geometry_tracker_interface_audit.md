# V57 Reference Geometry / Tracker Interface Audit

## Summary

This audit did not train PPO and did not change planner behavior, rewards,
observation layout, checkpoint, algorithm, MPPI, or `config/level3.toml`.

It reran the fixed planner-integration smoke with the v55 zigzag-qualified
tracker checkpoint and used the existing trace fields to diagnose whether v56
failure is mainly a planner-reference problem, a tracker-following problem, or
both.

The evidence points to both, with planner-reference geometry first:

- phase3 -> phase4 always introduces a `0.74m` reference jump;
- the tracker is already about `0.78m` away from the new reference at cross
  entry;
- action delta spikes at the same transition;
- phase4 desired speed is `0.32m/s`, but actual near-plane gate-local X speed
  remains much higher;
- contact stays `20/20`.

Because the cross reference is not yet a gentle, continuous command, the next
change should be a planner-interface fix before starting v58 tracker retraining.

## Command

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 500 \
  --early-termination-step-threshold 50 \
  --trace-output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57_reference_geometry_tracker_interface_audit_500step_trace.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57_reference_geometry_tracker_interface_audit_500step_metrics.json
```

Compatibility checker:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage planner_integration_smoke \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57_reference_geometry_tracker_interface_audit_500step_metrics.json \
  --history-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_required_stage_history_through_zigzag.json \
  --require-prerequisites \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57_reference_geometry_tracker_interface_audit_500step_gate.json
```

The compatibility checker passed, but it remains a plumbing check only.

## Fixed Smoke Result

- config: unchanged `config/level3.toml`
- checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- seeds: `101-120`
- Level3 steps: `500`
- trace rows: `2456`
- terminal rows excluded from interface metrics: `20`

Headline result:

- gate0 pass: `2/20`, seeds `113, 120`
- first-gate progress: `19/20`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `level3_toml_diff_clean`: `true`

## Diagnostic Coverage

No new trace fields were required. The audit used existing per-step fields:

- reference position: `reference_x/y/z`;
- drone position: `pos_x/y/z`;
- phase: `phase_id`;
- desired speed: `desired_speed`;
- actual gate-local X speed: `gate_local_vx`;
- aperture error: `aperture_yz_error`;
- target-gate transition: `pre_target_gate`, `post_target_gate`;
- action: `action_roll/pitch/yaw/thrust`.

All interface metrics below exclude terminal contact rows.

## Reference Jumps

Reference jumps over all active rows are usually zero because the reference is
held between phase updates:

- all active rows median jump: `0.000m`
- all active rows max jump: `1.910m`

At phase transitions, jumps become large:

- phase-transition median jump: `0.430m`
- phase-transition p75 jump: `0.740m`
- phase-transition max jump: `1.910m`

At the key phase3 -> phase4 transition:

- count: `9`
- reference jump median: `0.740m`
- reference jump min/max: `0.740m / 0.740m`

This is deterministic evidence of an abrupt cross-entry reference change.

Largest phase-transition jumps:

- seed `120`, phase4 -> phase1 after gate pass: `1.910m`
- seed `113`, phase4 -> phase2 after gate pass: `0.922m`
- all phase3 -> phase4 transitions: `0.740m`

The post-pass jumps are less relevant for first-gate failure; the phase3 -> 4
jump is the important one because it happens before most contacts.

## Reference-To-Drone Error

Reference-to-drone error is large near the cross command:

- all active median: `0.599m`
- phase3 median: `0.531m`
- phase4 median: `0.664m`
- near phase3/4 median: `0.620m`
- reasonable cross rows median: `0.664m`

At phase3 -> phase4 transition:

- median reference error: `0.783m`
- max reference error: `0.794m`

The planner is asking the tracker to jump to a reference that is about
`0.78m` away at the exact moment it asks for the precise cross behavior.

## Desired Speed Versus Actual Gate-Local X Speed

Phase4 desired speed is constant:

- desired speed: `0.32m/s`

Actual near-plane phase4 speed remains high:

- median absolute gate-local X speed: `0.522m/s`
- p75: `0.695m/s`
- max: `0.809m/s`

Reasonable-cross rows were defined as:

```text
phase4
abs(gate_local_x) < 0.35
desired_speed <= 0.35
aperture_yz_error <= 0.25
terminal rows excluded
```

There were `192` reasonable-cross rows across seeds
`101, 102, 109, 111, 113, 115, 117, 119, 120`.

Among them, `103/192` rows still had actual gate-local speed above the braking
screen:

```text
abs(gate_local_vx) > max(0.50, desired_speed + 0.15)
```

Fast reasonable-cross seeds:

```text
101, 102, 111, 113, 115, 117, 119, 120
```

This is evidence that the tracker is not slowing enough under the current
interface. But because the cross reference is already a `0.74m` jump with
`~0.78m` reference error, it is not yet fair to call the reference command
reasonable enough to justify tracker retraining as the immediate first fix.

## Aperture Error Near Phase3/Phase4

Phase4 aperture alignment is not grossly wrong:

- phase4 aperture median: `0.153m`
- phase4 aperture p75: `0.180m`
- near phase4 aperture max: `0.218m`

Near phase3/4 includes many align rows that are still not centered:

- near phase3/4 aperture median: `0.422m`
- near phase3/4 aperture p75: `0.658m`

Interpretation: cross-entry alignment is acceptable when phase4 begins, but the
interface still produces a large positional reference jump and high actual
cross speed.

## Phase3 -> Phase4 Timing

The phase3 -> phase4 transition happened for 9 seeds:

```text
101, 102, 109, 111, 113, 115, 117, 119, 120
```

Transition statistics:

- gate-local X median: `-0.330m`
- gate-local X range: `-0.334m` to `-0.164m`
- aperture error median: `0.172m`
- aperture error p75: `0.181m`
- actual absolute gate-local X speed median: `0.265m/s`
- desired speed: `0.32m/s`
- reference error median: `0.783m`
- action delta median: `0.727`

The transition criteria are not obviously too late or too off-center. The
problem is what happens at transition: the reference jumps, action changes
sharply, and the tracker later fails to brake enough.

## Overshoot Past Gate Plane Without Target-Gate Transition

Same-target overshoot rows with `gate_local_x > 0`:

- rows: `231`
- seeds: `104, 106, 110`
- max overshoot: `0.687m`

Most overshoot rows were not well aligned. Overshoot with
`aperture_yz_error <= 0.30` happened only for seed `106`:

- rows: `28`
- max same-target `gate_local_x`: `0.687m`

This supports both interpretations:

- planner/tracker can cross the plane without satisfying environment gate
  semantics;
- the current interface does not reliably turn near-plane approach into a
  valid gate pass.

## Action Norm And Action Delta

Action norm:

- active all median: `0.552`
- near phase3/4 median: `0.552`
- reasonable-cross median: `0.584`
- reasonable-cross p95: `0.873`
- reasonable-cross max: `1.019`

Action delta:

- active all median: `0.169`
- near phase3/4 median: `0.189`
- reasonable-cross median: `0.169`
- reasonable-cross p95: `0.373`
- reasonable-cross max: `0.820`

At phase3 -> phase4 transition:

- action delta median: `0.727`
- max: `0.820`

This action discontinuity lines up with the `0.74m` reference jump and is a
strong sign that the current interface is too abrupt.

## Seed-Level Pattern

Passed gate0 then contacted later:

```text
113, 120
```

Immediate/early contact:

```text
114, 118
```

Notable same-target overshoot:

```text
104, 106, 110
```

High-speed reasonable-cross failures:

```text
101, 102, 111, 115, 117, 119
```

No-first-gate-progress seed:

```text
112
```

## Diagnosis

Planner reference problem:

- phase3 -> phase4 reference jump is always `0.74m`;
- transition reference error is about `0.78m`;
- transition action delta is large;
- the cross command is not a small, continuous reference update.

Tracker problem:

- even with `desired_speed = 0.32m/s`, actual phase4 gate-local X speed is often
  `0.52m/s` to `0.70m/s`;
- many rows that are aligned well enough still move too fast;
- contact remains `20/20`.

Main conclusion:

```text
Both are involved, but fix planner-reference continuity first.
```

Reason: v58 tracker retraining should be based on a planner-like command that is
already smooth and physically trackable. The current phase3 -> phase4 reference
jump is too large to fairly isolate tracker capability.

## Recommended Next Action

Propose exactly one planner-interface fix:

```text
v57a_cross_entry_reference_continuity_clamp
```

One allowed change:

```text
At phase3 -> phase4, replace the instantaneous 0.74m reference jump with a
continuity-clamped cross-entry reference. The first phase4 reference should be
advanced only a short distance from the previous phase3 reference, then roll
toward aperture/post-gate over subsequent steps while keeping desired_speed
0.32m/s and preserving target_gate-only pass semantics.
```

Acceptance for the next smoke should include:

- phase3 -> phase4 reference jump median materially below `0.74m`;
- phase3 -> phase4 action delta lower than the current `0.727` median;
- no phase5/same-target recover rows;
- `config/level3.toml` unchanged;
- fixed seeds `101-120`, 500 steps;
- gate0 pass/contact should not regress further.

v58 tracker training should remain deferred until after this continuity fix is
tested. If the continuity-clamped reference is gentle and actual gate-local
speed still remains high with contact, then the evidence would support
`v58_tracker_planner_like_reference_training`.
