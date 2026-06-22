# Level3 PPO Stage 2 Audit After Loop014

## Verdict

Hold automatic training.

The loop has enough evidence to stop blind reward-only cycling and enough Stage
2 evidence to avoid launching another structural or observation experiment
without explicit approval. The current global best remains loop010, but it is a
weak and non-robust result, not a solved Level3 controller.

Current incumbent:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Incumbent hard-evaluator metrics:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
target = success_rate >= 0.60 and mean_time_s_success <= 7.0
```

This packet does not approve a new training run. It records the next decision
boundary for Codex-supervised loop work.

## Stage 1 Exhaustion Still Holds

The earlier structural escalation packet after loop007 is still valid:

```text
experiments/level3_ppo_loop/research/2026-06-18_structural_escalation_review_after_loop_007.md
```

It established:

| Requirement | Result |
| --- | --- |
| At least 6 evaluated reward-only trials | passed: loops 001, 002, 004, 005, 006, 007 |
| At least 4 distinct reward hypotheses | passed: 6 signatures |
| At least 120M evaluated reward-only steps | passed: about 210M command timesteps |
| At least 4 consecutive no-improvement trials | passed |
| Target unmet | passed |
| W&B reward-to-evaluator conversion absent | passed |
| Subagent agreement | passed |

The later loop014 reward-only branch did not overturn this conclusion.

## Stage 2 Evidence Since Escalation

| Trial / diagnostic | Change tested | Best hard-eval result | Decision |
| --- | --- | --- | --- |
| loop008 | gate0 sensor-range staging | success `0.00`, gates `0.75`, crash `1.00` | rollback / reject |
| loop009 | gate-box reward geometry alignment | success `0.00`, gates `0.75`, crash `1.00` | rollback / reject |
| parity diagnostics | observation/event and action scaling checks | parity issue fixed; action scaling clean | keep fixes, do not count as solved |
| loop010 | no train-only robustness wrappers | success `0.05`, time `5.64`, gates `0.80`, crash `0.95` | current best, weak signal |
| loop011 | soft gate / safety continuation | success `0.00`, gates `0.85`, crash `1.00` | reject |
| loop014 | loop010 gate retention plus obstacle safety | success `0.00`, gates `0.75`, crash `1.00` | reject |

The only non-zero success came from loop010, and the result was fragile:
20-seed success was `0.05`; the later 100-seed re-evaluation showed only a weak
`0.01` success signal. That is useful evidence that the no-train-wrapper branch
can sometimes finish, but it is far from the Level3 target.

## Loop014 Taxonomy Result

Loop014 did not fail because it needed a few more timesteps. Its best evaluated
checkpoint crashed in all 40 taxonomy episodes.

```text
episodes = 40
successes = 0
crashes = 40
crash_rate = 1.00
```

Crash distribution compared with the loop010 incumbent:

| Metric | Loop010 incumbent | Loop014 failed branch |
| --- | ---: | ---: |
| Successes | `0 / 40` | `0 / 40` |
| Crashes | `40 / 40` | `40 / 40` |
| Crashes targeting gate 0 | `17` | `18` |
| Crashes targeting gate 1 | `18` | `16` |
| Crashes targeting gate 2 | `5` | `6` |
| `gate_0_top` likely crashes | `10` | `4` |
| `obstacle_0` likely crashes | `6` | `11` |

Interpretation: loop014 shifted some crashes away from the gate top and into
obstacle0, but it did not move failures later into the course and did not
increase success.

## Geometry Bottleneck

The latest first-gate geometry sample for `level3_dr.toml` remains hard:

```text
gate0_inside_sensor_range_xy_rate = 0.17
obstacle0_corridor_lt_0p2_rate = 0.348
obstacle0_corridor_lt_0p4_rate = 0.672
gate0_horizontal_distance_median = 1.287
gate0_horizontal_distance_p95 = 2.107
```

This is the core practical problem: many starts put gate0 outside the current
local sensing range while obstacle0 is often close to the start-to-gate
corridor. Scalar reward changes can change preferences, but they cannot make an
invisible or under-specified first-gate geometry easier to infer.

## Current Loop Rule

Do not launch another automatic train/evaluate chunk from the current hold
state.

Allowed next actions:

1. User explicitly approves one low-confidence reward-only probe.
2. User explicitly approves a new Stage 2 structural packet.
3. Codex performs more read-only analysis, W&B analysis, or code diagnosis.

Disallowed without explicit approval:

- observation layout changes;
- PPO/network/algorithm changes;
- reward-channel additions or disabled reward-channel activation;
- train/eval environment changes;
- multi-iteration unattended training;
- continuing loop014 checkpoints.

## Low-Confidence Reward-Only Probe, If User Insists

This is the only remaining distinct active-reward hypothesis that does not
repeat loop011 or loop014 too closely:

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

It must use relaxed reward bounds because `cmd_tilt_coef=1.8` is above the
normal conservative bound of `1.6`. It should be run as one bounded chunk only,
then analyzed before any continuation.

Acceptance rule:

- accept only if `success_rate > 0.05`, or
- accept if `crash_rate < 0.95` with `mean_gates >= 0.80` and W&B
  `passed_gate_rate` / `finished_rate` conversion.

Reject if:

- `success_rate == 0.0`;
- `mean_gates < 0.80`;
- crashes stay concentrated at gates 0/1 without a new conversion signal;
- W&B reward improves but evaluator metrics do not.

## Recommended Goal Directive

Use this directive only after the user decides which lane to approve:

```text
Use $level3-ppo-loop in /home/aojili/lsy_drone_racing. Read AGENTS.md,
experiments/level3_ppo_loop/state.json, and
experiments/level3_ppo_loop/research/2026-06-18_stage2_after_loop014_escalation_audit.md
first. Do not run scripts/level3_ppo_loop.py with --max-iterations > 1.
Before any training, dry-run the exact command. After any completed
train/evaluate chunk, run scripts/analyze_level3_ppo_trial.py with W&B online,
spawn separate evaluator/W&B/reward-synthesis reviewers, update state.json, and
stop unless the hard evaluator improves over loop010. Keep disabled reward
channels at zero. Do not change PPO, observation layout, network, algorithm,
reward channel set, or training structure unless I explicitly approve a named
Stage 2 structural packet. The loop currently has a state-level hold guard; do
not pass --override-state-hold unless this goal text explicitly approves the
next lane. For reward-only runs, --override-state-hold must be paired with the
explicit reward --param list; for structural runs, it must be paired with the
approved structural command and --approved-hypothesis-packet.
```

For the low-confidence reward-only lane, append:

```text
I approve exactly one 30M reward-only relaxed-bounds probe from the current
loop010 best checkpoint using the coefficients listed in the Stage 2 audit
packet. Attach that packet with --research-packet, use W&B project
ADR-PPO-Racing-Level3, and stop after analysis. Do not continue automatically.
Use --override-state-hold only for that single approved probe.
```

For a structural lane, replace the append text with a named Stage 2 packet and
explicitly describe the allowed structural change before running anything.
