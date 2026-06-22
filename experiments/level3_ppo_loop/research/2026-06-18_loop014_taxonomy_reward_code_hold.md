# Level3 PPO Diagnosis: Loop014 Taxonomy + Reward-Code Hold

## Decision

Hold automatic training. Do not launch another 30M train/evaluate chunk yet.

The latest failed branch, `level3_loop_014_loop010_gate_retention_obstacle_safety`,
did not merely need more timesteps. It changed the crash distribution without
improving the hard evaluator.

Current global best remains:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Current best metrics:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
```

## New Diagnostics

Loop014 40-seed crash taxonomy:

```text
experiments/level3_ppo_loop/diagnostics/level3_loop_014_25M_gate_retention_obstacle_safety_crash_taxonomy_summary.json
```

Loop014 first-gate geometry overlap:

```text
experiments/level3_ppo_loop/diagnostics/level3_loop_014_25M_gate_retention_obstacle_safety_first_gate_geometry_summary.json
```

## Loop010 vs Loop014 Crash Taxonomy

Both 40-seed taxonomy runs had `0 / 40` success and `40 / 40` crashes.

| Metric | Loop010 incumbent | Loop014 failed branch |
| --- | ---: | ---: |
| Successes | `0 / 40` | `0 / 40` |
| Crashes | `40 / 40` | `40 / 40` |
| Crashes targeting gate 0 | `17` | `18` |
| Crashes targeting gate 1 | `18` | `16` |
| Crashes targeting gate 2 | `5` | `6` |
| `gate_0_top` likely crashes | `10` | `4` |
| `obstacle_0` likely crashes | `6` | `11` |
| `obstacle_1` likely crashes | `5` | `5` |

Interpretation:

- Loop014 did not push failures later into the track.
- It reduced one visible gate-top failure mode, but increased `obstacle_0`
  crashes.
- That is not hard-evaluator progress; it is a redistribution of early crashes.

## First-Gate Geometry Context

For `level3_dr.toml`, the sampled first-gate geometry remains hard:

```text
gate0_inside_sensor_range_xy_rate = 0.17
obstacle0_corridor_lt_0p2_rate = 0.348
obstacle0_corridor_lt_0p4_rate = 0.672
```

For loop014 target-gate-0 crashes:

```text
target0_crash_obstacle0_corridor_median = 0.247m
target0_crash_obstacle0_corridor_75p = 0.320m
```

This means a large share of early episodes starts with gate0 outside sensor
range and obstacle0 close to the start-to-gate corridor. Reward-only scaling
can change preferences, but it cannot reveal invisible gate state or create a
curriculum.

## Reward-Code Diagnosis

Active reward mechanics in `train_CleanRL_ppo_level3.py`:

- `gate_axis_coef`, `gate_stage_coef`, `gate_front_bonus`,
  `gate_back_bonus`, `gate_bonus`, and `finish_bonus` are the primary gate
  acquisition and completion drivers.
- `cmd_tilt_coef` directly penalizes commanded roll/pitch tilt via
  `(cmd_tilt / (pi / 2)) ** 2`.
- `d_act_xy_coef` and `d_act_th_coef` penalize action changes, not sustained
  command saturation.
- `rpy_coef` and `tilt_excess_coef` penalize actual attitude, but loop010/014
  actual tilt is not the main logged saturation; commanded tilt is.
- `obstacle_coef` only applies when `obstacle_dist < obstacle_margin`, using a
  squared penalty.
- `crash_penalty` is a sparse terminal penalty and does not teach a pre-crash
  avoidance path by itself.

Failed reward-only directions:

- Loop011 lowered gate pressure and slightly increased `cmd_tilt_coef`; success
  dropped to zero.
- Loop014 kept gate pressure but raised finish/crash/obstacle safety with only
  a small obstacle-margin increase; success stayed zero and obstacle0 crashes
  increased.
- The analyzer's generic lower-gate-pressure recommendation is not a new
  evidence-backed direction; it overlaps with already failed soft/low-pressure
  lanes.

## External Evidence

Recent obstacle-aware drone-racing work consistently treats gate traversal and
obstacle avoidance as a coupled, difficult trade-off:

- CRL-Drone-Racing reports that obstacle-rich racing needs multi-stage
  curriculum learning, domain randomization, and reward design that balances
  obstacle avoidance against gate passing:
  https://arxiv.org/html/2602.24030v1
- Learning Generalizable Policy for Obstacle-Aware Autonomous Drone Racing uses
  domain randomization over tracks and obstacles, and its reward combines
  progress/guidance, collision, waypoint passing, timeout, and velocity terms:
  https://arxiv.org/html/2411.04246v1
- MasterRacing frames cluttered drone racing as a balance between speed,
  collision avoidance, and exploration, and uses a soft-collision phase before
  hard-collision refinement:
  https://arxiv.org/html/2512.09571v1
- The CRL-Drone-Racing repository explicitly notes that developers are expected
  to design curricula for their tasks:
  https://github.com/SJTU-ViSYS-team/CRL-Drone-Racing

These sources do not justify silently changing this project to curriculum,
soft-collision, observation, or algorithm changes. They do support the local
conclusion that repeated scalar reward tweaks are unlikely to solve the current
Level3 failure without a new explicit escalation packet.

## Only Plausible Reward-Only Hypothesis

If the user explicitly asks to continue reward-only despite this hold, the only
distinct active-reward hypothesis not yet tested is a direct commanded-tilt and
wider-margin obstacle signal while preserving gate pressure:

```text
gate_stage_coef=14
gate_axis_coef=28
gate_bonus=220
gate_front_bonus=10
gate_back_bonus=45
finish_bonus=190
wrong_side_penalty=8
crash_penalty=55
obstacle_coef=5
obstacle_margin=0.38
timeout_penalty=80
time_penalty=0.01
act_coef=0.015
d_act_th_coef=0.075
d_act_xy_coef=0.08
cmd_tilt_coef=1.8
rpy_coef=0.75
tilt_limit_deg=38
tilt_excess_coef=14
```

Rationale:

- keep loop010 gate acquisition pressure intact;
- avoid repeating loop011's gate-softening failure;
- avoid loop014's sparse crash-penalty and tiny-margin obstacle change;
- directly target commanded tilt saturation;
- make obstacle penalty active earlier by increasing `obstacle_margin`.

Confidence: low. This should not be launched automatically from the current
hold state without user confirmation or a stronger decision packet, because it
may suppress gate acquisition and repeat earlier low-conversion failures.

## Stop / Acceptance Rules For Any Future Trial

Accept a future reward-only branch only if it improves over loop010 on hard
evaluator evidence:

- `success_rate > 0.05`, or
- `crash_rate < 0.95` with `mean_gates >= 0.80` and W&B gate/finish conversion.

Reject if:

- `success_rate == 0.0`,
- `mean_gates < 0.80`,
- crash remains concentrated at gates 0/1 without a new conversion signal, or
- W&B reward improves while `passed_gate_rate` and `finished_rate` stay flat.
