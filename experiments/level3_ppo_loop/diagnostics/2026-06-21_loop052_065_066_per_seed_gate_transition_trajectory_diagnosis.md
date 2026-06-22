# Loop052/065/066 Per-Seed Gate-Transition Diagnosis

Date: 2026-06-21

## Scope

Target hard eval remains `config/level3_dr.toml`. Level3 track geometry,
randomization, gates, and obstacles are unchanged.

This packet uses the reset-fixed crash-hotspot episode CSVs:

- `experiments/level3_ppo_loop/diagnostics/loop052_best_crash_hotspots_resetfix_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/loop065_v13_final_crash_hotspots_resetfix_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/loop066_v14_10m_crash_hotspots_resetfix_episodes.csv`

Evidence boundary: these CSVs classify the last valid endpoint before
termination. They are not full per-step trajectories. Official hard-eval CSVs
remain authoritative for success rate and best-checkpoint selection.

## Official Hard-Eval Anchor

| Trial | Best Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | --- | ---: | ---: | ---: | ---: |
| loop052 | final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop065 v13 | final | 0.15 | 1.25 | 0.85 | 6.393s |
| loop066 v14 | 10M | 0.10 | 1.25 | 0.90 | 6.400s |

Loop052 remains the global best.

## Endpoint Transition Classes

Classification rule:

- `success`: race finished.
- `pre_plane_obstacle`: obstacle endpoint with target-gate local x less than
  about `-0.75m`, meaning the failure happened well before the target gate
  plane.
- `near_gate_obstacle`: obstacle endpoint closer to the target-gate plane.
- `gate_side_frame`: left/right gate-frame endpoint.
- `gate_vertical_frame`: top/bottom gate-frame endpoint.
- `other_crash`: stand/bounds/unclear geometry.

| Trial | Success | Near-Gate Obstacle | Pre-Plane Obstacle | Side Frame | Vertical Frame | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| loop052 final | 3 | 6 | 3 | 4 | 3 | 1 |
| loop065 v13 final | 4 | 5 | 1 | 7 | 2 | 1 |
| loop066 v14 10M | 2 | 7 | 4 | 3 | 3 | 1 |

Interpretation:

- v13 moved failures toward gate side-frame contact. It did not improve the
  official hard-eval frontier.
- v14 reduced side-frame endpoints but increased obstacle endpoints and
  pre-plane obstacle failures. This matches the official crash regression.
- Neither v13 nor v14 shows a clean conversion improvement over loop052.

## Crash Target-Gate Distribution

| Trial | Gate 0 | Gate 1 | Gate 2 | Gate 3 |
| --- | ---: | ---: | ---: | ---: |
| loop052 final | 9 | 2 | 5 | 1 |
| loop065 v13 final | 9 | 4 | 2 | 1 |
| loop066 v14 10M | 8 | 5 | 4 | 1 |

Interpretation:

- loop052 still has many gate-0 failures, but it sometimes survives into
  later gates and finishes.
- v13 shifts more crashes to gate 1, often as side-frame contact.
- v14 keeps gate-0 pressure and increases gate-1/gate-2 obstacle failures.

## Per-Seed Transition Table

| Seed | loop052 gates / class / object | loop065 gates / class / object | loop066 gates / class / object |
| ---: | --- | --- | --- |
| 1 | 2 / near_gate_obstacle / obstacle_2 | 1 / gate_side_frame / gate_1_right | 2 / near_gate_obstacle / obstacle_2 |
| 2 | 0 / near_gate_obstacle / obstacle_0 | 1 / gate_side_frame / gate_1_left | 1 / near_gate_obstacle / obstacle_1 |
| 3 | 0 / gate_side_frame / gate_0_right | 0 / gate_side_frame / gate_0_right | 0 / near_gate_obstacle / obstacle_0 |
| 4 | 1 / near_gate_obstacle / obstacle_2 | 1 / near_gate_obstacle / obstacle_2 | 1 / gate_vertical_frame / gate_3_top |
| 5 | 2 / gate_side_frame / gate_2_left | 0 / gate_side_frame / gate_0_left | 0 / gate_side_frame / gate_0_left |
| 6 | 1 / pre_plane_obstacle / obstacle_3 | 1 / gate_side_frame / gate_1_left | 1 / pre_plane_obstacle / obstacle_3 |
| 7 | 0 / gate_vertical_frame / gate_0_bottom | 0 / gate_side_frame / gate_0_left | 1 / gate_vertical_frame / gate_0_top |
| 8 | 3 / pre_plane_obstacle / obstacle_0 | 3 / near_gate_obstacle / obstacle_3 | 3 / pre_plane_obstacle / obstacle_0 |
| 9 | 0 / gate_side_frame / gate_0_right | 0 / gate_side_frame / gate_0_right | 0 / gate_side_frame / gate_0_right |
| 10 | 2 / gate_side_frame / gate_1_right | 3 / success /  | 2 / gate_side_frame / gate_1_right |
| 11 | 3 / success /  | 3 / success /  | 3 / success /  |
| 12 | 2 / gate_vertical_frame / gate_1_top | 2 / gate_vertical_frame / gate_1_top | 3 / success /  |
| 13 | 3 / success /  | 3 / success /  | 1 / pre_plane_obstacle / obstacle_3 |
| 14 | 0 / other_crash / gate_3_stand | 0 / other_crash / gate_3_stand | 0 / other_crash / gate_3_stand |
| 15 | 0 / near_gate_obstacle / obstacle_0 | 0 / near_gate_obstacle / obstacle_0 | 0 / near_gate_obstacle / obstacle_0 |
| 16 | 3 / success /  | 3 / success /  | 2 / near_gate_obstacle / obstacle_2 |
| 17 | 0 / gate_vertical_frame / gate_0_bottom | 0 / gate_vertical_frame / gate_0_bottom | 0 / gate_vertical_frame / gate_0_bottom |
| 18 | 0 / near_gate_obstacle / obstacle_0 | 0 / near_gate_obstacle / obstacle_0 | 0 / near_gate_obstacle / obstacle_0 |
| 19 | 2 / near_gate_obstacle / obstacle_1 | 2 / near_gate_obstacle / obstacle_1 | 2 / near_gate_obstacle / obstacle_1 |
| 20 | 0 / pre_plane_obstacle / obstacle_1 | 0 / pre_plane_obstacle / obstacle_1 | 0 / pre_plane_obstacle / obstacle_1 |

## Diagnosis

The endpoint evidence does not support another reward-number-only run:

- v13 adds side-frame pressure around gate 1.
- v14 shifts the failure toward obstacle and pre-plane obstacle contact.
- The successful seeds are not stable across reward variants.
- Several seeds are invariant failures across all three policies:
  `14`, `15`, `17`, `18`, `19`, and `20`.
- Seeds `13` and `16` are loop052 successes that v14 loses, which is a strong
  rejection signal for v14-style directional pass conversion.

This is not enough to choose a new training lane safely. The endpoint data says
where runs terminate, but not whether the root cause is:

- missing local obstacle-route observation;
- unsafe control saturation or overshoot before the gate plane;
- reward encouraging close-but-illegal approaches;
- a small set of hard geometry seeds dominating the frontier.

## Recommendation

Decision: `hold_for_more_analysis`.

Do not launch hidden512 follow-up, GRU maturation, v14 continuation, or a
simple direct-aperture/soft-centerline/frame-clearance reward repeat.

Next diagnostic artifact should add per-step traces for the last `1.5s-2.0s`
before termination on loop052 final, loop065 final, and loop066 10M. It should
record target-gate local position/velocity, nearest obstacle distance,
nearest gate-frame distance, command/action magnitude, tilt, wrong-side
approach indicator, gate-plane crossing indicator, and target-gate index.

The next training lane should remain blocked until that trace-level artifact
can choose one explicit axis: observation, controller/action smoothing,
curriculum/seed triage, or continued hold.
