# Loop066 Audit: Plateau With No Conversion

## Context

Loop066 tested:

`v14_mlp_loop052_constant_lr_directional_pass_conversion_guard`

It started from loop052 final, kept the v5 local-obstacle observation, 2x256
Tanh MLP, constant `learning_rate=5e-5`, `anneal_lr=False`, and nominal
safety/control numbers. It reduced raw gate pressure and moved weight toward
directional front/back pass conversion plus wrong-side guarding.

Hard eval remained on unchanged `config/level3_dr.toml`.

## Hard-Eval Comparison

| Trial | Best Checkpoint | Success | Mean Gates | Crash | Mean Successful Time | Action Delta | Cmd Tilt Over Limit |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| loop052 | final | 0.20 | 1.40 | 0.80 | 6.975s | 0.284 | 0.306 |
| loop065 v13 | final | 0.15 | 1.25 | 0.85 | 6.393s | 0.324 | 0.431 |
| loop066 v14 | 10M | 0.10 | 1.25 | 0.90 | 6.400s | 0.281 | 0.291 |

Loop066 does not exceed loop052 on success, mean gates, or crash. It also
regresses from loop065 on success and crash.

## W&B Conversion Evidence

| Metric | loop065 v13 Tail | loop065 Trend | loop066 v14 Tail | loop066 Trend |
| --- | ---: | --- | ---: | --- |
| `race/passed_gate_rate` | 0.007928 | flat | 0.007568 | flat |
| `race/finished_rate` | 0.000208 | flat | 0.000112 | flat |
| `race/gate_plane_cross_rate` | 0.002661 | flat | 0.002899 | flat |
| `race/gate_plane_center_hit_rate` | 0.000220 | flat | 0.000203 | flat |
| `race/wrong_side_gate_rate` | 0.022992 | flat | 0.023855 | flat |
| `race/gate_frame_pressure` | 1.011303 | up | 1.200687 | up |
| `reward_components/gate_plane` | 0.000000 | flat | 0.000000 | flat |
| `reward_components/wrong_side` | -0.183936 | down | -0.333964 | down |

The critical failure is not PPO inactivity. Both v13 and v14 had constant
learning rate and nonzero PPO update pressure. The failure is behavioral:
approach/gate pressure does not convert into center-hit, plane-cross, passed
gate, or finished events.

## Prior Related Lanes

Existing centered-plane and followthrough reward structures have already been
tested and did not beat loop052:

| Trial | Reward Structure | Success | Mean Gates | Crash |
| --- | --- | ---: | ---: | ---: |
| loop035 | `legacy_frame_clearance` | 0.00 | 0.85 | 1.00 |
| loop036 | `decoupled_frame_clearance` | 0.10 | 1.40 | 0.85 |
| loop037 | `decoupled_frame_clearance` maturation | 0.00 | 0.60 | 0.85 |
| loop039 | `direct_aperture` | 0.00 | 1.00 | 1.00 |
| loop040 | `soft_centerline_followthrough` | 0.10 | 1.15 | 0.90 |
| loop056 | `soft_centerline_followthrough` from loop052 | 0.15 | 1.20 | 0.85 |

This means the next step should not be a simple repeat of `direct_aperture` or
`soft_centerline_followthrough` with only cosmetic number changes.

## Interpretation

The narrow v14 hypothesis is rejected. The broader reward-number axis around
raw gate pressure, directional front/back conversion, and previously tested
centered-plane reward structures is currently plateaued.

The best current checkpoint remains loop052:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

## Required Next Analysis Before More Training

Before launching another training run, run a targeted conversion-diagnosis pass
that answers:

1. On the loop052 successful and crashing seeds, where is the crash relative to
   gate plane, gate frame, obstacles, and target gate index?
2. For loop065 and loop066, did wrong-side approaches or gate-frame pressure
   increase before the crash?
3. Are the surviving successful episodes faster because they cut unsafe lines,
   or because the policy genuinely improves pass conversion?
4. Which existing structure is the right next axis: observation, controller
   action smoothing, reward structure, or evaluator/trajectory-specific failure
   repair?

Do not start a new 20M run until that diagnostic packet exists.
