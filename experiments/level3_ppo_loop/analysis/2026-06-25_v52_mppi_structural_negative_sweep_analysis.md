# V52 MPPI Structural Negative Sweep Analysis

Date: 2026-06-25

Lane: `v52_mppi_oracle_teacher_level3`

Target config: unchanged `config/level3.toml`

## Summary

This round stayed MPPI-only. It did not launch PPO training, BC, DAgger,
teacher data generation, or PPO fine-tuning.

No controller change from this round is retained. The source tree was restored
to the previous v33/v52 MPPI baseline after each negative test.

Current retained MPPI baseline:

- smoke `101-105`: `0%` success, `0.80` mean gates, `100%` crash;
- dev `1-10`: `0%` success, `0.20` mean gates, `100%` crash;
- smoke endpoint classes: `{"gate_side_frame": 2, "near_gate_obstacle": 3}`;
- dev endpoint classes: `{"gate_side_frame": 8, "gate_vertical_frame": 2}`.

The MPPI result remains below the PPO frontier and must not be recorded as PPO
success.

## What Was Tested

Additional negative tests after the velocity-diagnostics packet:

| Trial | Idea | Smoke success | Smoke mean gates | Crash | Timeout | Decision |
|---|---:|---:|---:|---:|---:|---|
| `v35_gate_frame_velocity_guide` | gate-frame velocity guide | `0%` | `0.00` | `100%` | `0%` | reject |
| `v36_gate_frame_hold_center` | hold center before crossing | `0%` | `0.00` | `20%` | `80%` | reject |
| `v37_gate_frame_soft_hold` | softer hold center | `0%` | `0.00` | `20%` | `80%` | reject |
| `v38_gate_frame_fast_cross` | faster gate-frame crossing | `0%` | `0.00` | `100%` | `0%` | reject |
| `v39_gate_frame_clearance_cost` | strong gate-frame clearance cost | `0%` | `0.40` | `100%` | `0%` | reject |
| `v40_light_gate_frame_clearance_cost` | light gate-frame clearance cost | `0%` | `0.80` | `100%` | `0%` | reject after dev regressed to `0.10` mean gates |
| `v41_near_plane_velocity_gate` | only near-plane velocity gate | `0%` | `0.60` | `100%` | `0%` | reject |
| `v42_rp45_baseline_guide` | raise roll/pitch authority to 45 deg | `0%` | `0.60` | `100%` | `0%` | reject |
| `v43_alpha1_baseline_guide` | remove action low-pass | `0%` | `0.60` | `100%` | `0%` | reject |
| `v44_low_temp_small_elite` | lower MPPI temperature and elite fraction | `0%` | `0.60` | `100%` | `0%` | reject |
| `v45_samples1024_baseline_guide` | increase samples to 1024 | `0%` | `0.20` | `100%` | `0%` | reject |
| `v46_gate_axis_pure_pursuit_guide` | gate-axis pure-pursuit path guide | `0%` | `0.00` | `60%` | `40%` | reject |
| `v47_yaw_aligned_acc_mapping` | yaw-aligned acceleration mapping | `0%` | `0.40` | `100%` | `0%` | reject |
| `v48_gate_frame_phase_velocity_guide` | phase-based gate-frame velocity controller | `0%` | `0.20` | `80%` | `20%` | reject |
| `v49_attitude_response_rollout` | first-order attitude-response rollout | `0%` | `0.40` | `100%` | `0%` | reject |
| `v50_multibranch_gate_guide` | center/left/right/high/low guide proposals | `0%` | `0.60` | `100%` | `0%` | reject |

## Interpretation

The current v52 local MPPI controller is not compute-limited. Increasing sample
count and making MPPI selection more aggressive made performance worse.

The current controller is also not fixed by local guide patches. Gate-frame
velocity control, near-plane speed limiting, pure pursuit, yaw-aligned mapping,
and multi-branch guide proposals all failed to exceed the retained baseline.

The consistent failure mode is still contact near the first or next gate:

- side-frame and vertical-frame contact;
- near-gate obstacle contact;
- no nonzero success on smoke or dev;
- no reason to run full validation yet.

This points to a deeper controller mismatch:

- the rollout model is too approximate for the real `first_principles` attitude
  dynamics and contact geometry;
- the guide still dominates the search, so MPPI is not doing broad
  trajectory-level planning;
- obstacle avoidance is not truly gate-aware;
- the local action-sequence horizon is not enough to solve the randomized
  corridor/gate/obstacle geometry reliably.

## Decision

Decision: `launch_named_structural_lane`

Reject continued v52 local guide/cost/sample tuning as the immediate path.

Open a new MPPI-only structural lane:

```text
v53_level3_mppi_controller_redesign
```

The next lane should still keep `config/level3.toml` immutable and still avoid
PPO/teacher-data work. Its purpose is to test a stronger MPPI/controller
architecture, not another scalar tweak.

Recommended v53 priorities:

1. Build a deterministic gate-aware geometric controller baseline that can pass
   single gates more reliably before wrapping it in MPPI.
2. Add a contact-aware planner that chooses a feasible aperture point before
   obstacle detouring; obstacle avoidance must not push the aim outside the gate
   opening.
3. If keeping MPPI, use trajectory-level proposals over waypoint/pass-point
   branches rather than only action noise around one guide.
4. Consider simulator-in-the-loop or a more faithful surrogate only after the
   geometric controller can reliably avoid first-gate frame contact.

Teacher-data generation remains closed until MPPI has useful hard-eval
evidence.
