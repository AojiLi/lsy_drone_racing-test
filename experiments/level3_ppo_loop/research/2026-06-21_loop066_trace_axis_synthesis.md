# Loop066 Trace-Axis Synthesis

Date: 2026-06-21

## Decision Axis

Chosen next axis: `curriculum/seed-geometry triage`.

Do not launch training yet. The next required artifact is a named structural
lane packet that defines a training-only seed/geometry curriculum and explains
how it differs from the failed loop032 no-wrapper curriculum.

Hard eval remains `config/level3_dr.toml`; do not modify the Level3 target
track geometry, randomization, gates, or obstacles.

## Inputs

Trace-level diagnostic:

- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_report.md`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_summary.json`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_trace.csv`

Prior loop066 hold packet:

- `experiments/level3_ppo_loop/decisions/2026-06-21_loop066_post_diagnosis_hold_for_transition_traces.md`

Prior curriculum rejection:

- `experiments/level3_ppo_loop/decisions/2026-06-20_hold_after_loop032_v5_curriculum_domain_gap_diagnosis.md`

## Official Anchor

Official hard eval remains authoritative:

| Trial | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| loop052 final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop065 final | 0.15 | 1.25 | 0.85 | 6.393s |
| loop066 10M | 0.10 | 1.25 | 0.90 | 6.400s |

Loop052 remains the global best.

## Trace Findings

Trace replay reproduces the official ranking: loop052 is best, loop065
regresses, and loop066 regresses further.

Endpoint classes:

| Checkpoint | Success | Mean Gates | Endpoint Pattern |
| --- | ---: | ---: | --- |
| loop052 final | 0.20 | 1.40 | side-frame and near-obstacle crashes, 4 success seeds |
| loop065 final | 0.15 | 1.25 | more near-obstacle/side-frame failures, 3 success seeds |
| loop066 10M | 0.10 | 1.25 | more obstacle and pre-plane obstacle failures, 2 success seeds |

Control saturation is not the primary next axis:

| Checkpoint | Final-Window Cmd Tilt Over Limit | Final-Window Action Saturation |
| --- | ---: | ---: |
| loop052 final | 0.133 | 0.126 |
| loop065 final | 0.180 | 0.132 |
| loop066 10M | 0.104 | 0.121 |

Interpretation: v14 has lower command-tilt over-limit and slightly lower
action saturation than loop052, but worse hard-eval success and crash. That
does not support another action-smoothing or controller-limit lane as the next
move.

Reward-number continuation is also unsupported:

- v13/v14 changed conversion reward numbers but did not improve hard eval.
- v14 loses loop052 success seeds `13` and `16`, both becoming obstacle
  failures.
- The trace does not show a stable wrong-side or gate-plane center-hit signal
  that a simple direct-aperture, soft-centerline, or frame-clearance reward
  repeat would repair.

## Why The Next Axis Is Curriculum/Seed Geometry

Several seeds are structurally hard across all three policies:

- seed `14`: all three fail at 0 gates with unclear/stand-like endpoint;
- seed `15`: all three fail at 0 gates near obstacle 0;
- seed `17`: all three fail at 0 gates on gate-0 vertical frame;
- seed `18`: all three fail at 0 gates near obstacle 0;
- seed `20`: all three fail at 0 gates before the gate plane near obstacle 1.

Other seeds show that reward changes reshuffle outcomes rather than improving
the frontier:

- seed `13`: loop052 and loop065 finish, loop066 fails at 1 gate near obstacle 3;
- seed `16`: loop052 and loop065 finish, loop066 fails at 2 gates near obstacle 2;
- seed `2`: loop052 fails at 0 gates, v13/v14 reach 1 gate but still fail near
  obstacle 1.

The most likely bottleneck is not pure policy capacity, PPO instability, or
missing pass-reward scale. It is a geometry-conditioned route-learning problem:
the controller sometimes knows how to fly the track, but specific randomized
gate/obstacle corridors remain unsolved and reward variants trade one seed set
against another.

## Difference From Failed Loop032 Curriculum

Do not repeat loop032.

Loop032 used `level3_dr_stage2_no_train_wrappers.toml` and regressed to
`0.00` success with severe command saturation under hard eval. The next
curriculum packet must differ in all of the following ways:

- keep deploy/domain-randomization wrappers unless the packet explicitly proves
  they are the cause;
- start from loop052 global best or a checkpoint with comparable hard-eval
  behavior, not from the older loop020 branch;
- target seed/geometry cases revealed by the trace, especially early
  obstacle-route and first/second-gate corridor failures;
- hard-evaluate every milestone on unchanged `config/level3_dr.toml`;
- include a rollback rule if hard-eval success, mean gates, or crash regresses
  relative to loop052.

## Required Next Packet

Before training, write a named structural packet under
`experiments/level3_ppo_loop/decisions/` with:

- lane name;
- training-only config or sampler change;
- exact difference from `config/level3_dr.toml`;
- checkpoint start point;
- reward/controller/PPO numbers;
- W&B run naming;
- milestone eval plan;
- hard rollback conditions.

Until that packet exists and the orchestrator has a matching runnable
structural hypothesis, the correct decision remains `hold_for_more_analysis`.
