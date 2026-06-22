# Loop052/065/066 Conversion Diagnosis

## Scope

This packet diagnoses why the latest reward-number lanes did not improve
Level3 hard eval. It does not approve a new training run by itself.

Hard eval remains `config/level3_dr.toml`. Do not modify track geometry,
randomization, gates, or obstacles.

## Inputs

Official hard-eval summaries:

- `experiments/level3_ppo_loop/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_eval_summary.csv`
- `experiments/level3_ppo_loop/level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m_eval_summary.csv`
- `experiments/level3_ppo_loop/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_eval_summary.csv`

W&B analysis packets:

- `experiments/level3_ppo_loop/analysis/level3_loop_065_structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m_analysis.json`
- `experiments/level3_ppo_loop/analysis/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_analysis.json`

Crash-hotspot diagnostics:

- `experiments/level3_ppo_loop/diagnostics/loop052_best_crash_hotspots_resetfix_summary.json`
- `experiments/level3_ppo_loop/diagnostics/loop065_v13_final_crash_hotspots_resetfix_summary.json`
- `experiments/level3_ppo_loop/diagnostics/loop066_v14_10m_crash_hotspots_resetfix_summary.json`

Note: crash-hotspot diagnostics are explanatory only. The official evaluator
CSV remains authoritative for success rate and best-checkpoint selection.

## Official Hard-Eval Result

| Trial | Best Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | --- | ---: | ---: | ---: | ---: |
| loop052 | final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop065 v13 | final | 0.15 | 1.25 | 0.85 | 6.393s |
| loop066 v14 | 10M | 0.10 | 1.25 | 0.90 | 6.400s |

Conclusion: both v13 and v14 regress relative to loop052 on success, mean gates,
and crash rate. Faster success time is not useful because it comes from fewer
successful seeds.

## W&B Conversion Result

| Metric | loop065 Tail | loop065 Trend | loop066 Tail | loop066 Trend |
| --- | ---: | --- | ---: | --- |
| `race/passed_gate_rate` | 0.007928 | flat | 0.007568 | flat |
| `race/finished_rate` | 0.000208 | flat | 0.000112 | flat |
| `race/gate_plane_cross_rate` | 0.002661 | flat | 0.002899 | flat |
| `race/gate_plane_center_hit_rate` | 0.000220 | flat | 0.000203 | flat |
| `race/wrong_side_gate_rate` | 0.022992 | flat | 0.023855 | flat |
| `race/gate_frame_pressure` | 1.011303 | up | 1.200687 | up |
| `reward_components/gate_plane` | 0.000000 | flat | 0.000000 | flat |
| `reward_components/wrong_side` | -0.183936 | down | -0.333964 | down |

Conclusion: PPO was updating, but pass/finish/plane-cross conversion did not
improve. v14 increased wrong-side penalty, but wrong-side reward became more
negative and gate-frame pressure increased.

## Crash-Hotspot Pattern

### loop052 best

Crash-hotspot summary:

- target gate 0 crashes: 9
- target gate 1 crashes: 2
- target gate 2 crashes: 5
- target gate 3 crashes: 1
- top likely objects:
  - `obstacle_0`: 4
  - `gate_0_bottom`: 2
  - `gate_0_right`: 2
  - `obstacle_1`: 2
  - `obstacle_2`: 2

Interpretation: loop052 still has many early gate-0 failures, but when it
survives gate 0 it can sometimes reach later gates and finish.

### loop065 v13

Crash-hotspot summary:

- target gate 0 crashes: 9
- target gate 1 crashes: 4
- target gate 2 crashes: 2
- target gate 3 crashes: 1
- top likely objects:
  - gate-frame left/right objects increase around gate 0 and gate 1
  - `obstacle_0`: 2
  - `obstacle_1`: 2

Target-gate-1 crash mean local position:

- x: -0.243
- y: -0.074
- z: 0.015

Interpretation: v13 moved some failures closer to a centered gate-1 approach,
but did not convert that into passed-gate events. This matches W&B:
`gate_plane_center_hit_rate` remained nearly zero. Raw gate pressure appears to
pull the vehicle toward the gate corridor without producing robust, legal
crossing.

### loop066 v14

Crash-hotspot summary:

- target gate 0 crashes: 8
- target gate 1 crashes: 5
- target gate 2 crashes: 4
- target gate 3 crashes: 1
- top likely objects:
  - `obstacle_0`: 4
  - `obstacle_1`: 3
  - `obstacle_2`: 2
  - `obstacle_3`: 2

Target-gate-1 crash mean local position:

- x: -1.566
- y: -0.443
- z: 0.056

Interpretation: v14 worsened the transition into gate 1. It crashes far before
the gate plane and later-gate obstacle objects become more prominent. The
directional pass-conversion reward did not solve the conversion gap and may
have reduced useful acquisition pressure.

## Prior Reward-Structure Evidence

The proposed gate-plane center-hit direction is not new in this codebase. Prior
lanes already tested related structures:

| Trial | Reward Structure | Success | Mean Gates | Crash |
| --- | --- | ---: | ---: | ---: |
| loop035 | `legacy_frame_clearance` | 0.00 | 0.85 | 1.00 |
| loop036 | `decoupled_frame_clearance` | 0.10 | 1.40 | 0.85 |
| loop037 | `decoupled_frame_clearance` maturation | 0.00 | 0.60 | 0.85 |
| loop039 | `direct_aperture` | 0.00 | 1.00 | 1.00 |
| loop040 | `soft_centerline_followthrough` | 0.10 | 1.15 | 0.90 |
| loop056 | `soft_centerline_followthrough` from loop052 | 0.15 | 1.20 | 0.85 |

Conclusion: do not launch a simple v15 that only repeats direct aperture,
soft centerline, or frame-clearance reward with minor number changes.

## Diagnosis

The current plateau is not primarily:

- too few training steps for v13/v14;
- learning-rate annealing;
- PPO update collapse;
- missing centered-plane metric support.

The current plateau is more likely:

- the policy approaches the first one or two gates but fails to turn approach
  into stable legal crossings;
- later-gate obstacle interactions dominate when a reward change gets past
  early gate 0;
- event-only center-hit rewards are too sparse to repair this without a more
  informative observation/controller/trajectory diagnostic.

## Recommended Next Move

Hold training until a new structural hypothesis is written that is materially
different from the already-failed direct-aperture, soft-centerline, and
frame-clearance lanes.

The most defensible next hypothesis should target one of:

1. Observation: expose a clearer local gate-corridor or obstacle-route signal
   that explains gate-1/gate-2 obstacle crashes.
2. Controller/action smoothing: reduce unsafe approach/control saturation
   without losing acquisition.
3. Curriculum or evaluation-seed triage: diagnose whether the same seed
   geometries repeatedly fail and design a training-only curriculum that still
   hard-evals on unchanged `level3_dr.toml`.

Do not start another 20M run from reward numbers alone.
