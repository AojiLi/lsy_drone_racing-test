# Level3 V50 Hidden512 Update-Pressure Plan

Status: proposed hidden512-family follow-up after loop119/loop120 completed
the v49 long-horizon read.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization
  changes.

Deployment remains:

```text
Level3 v5 observation/history
  -> 2x512 PPO Actor
  -> roll / pitch / yaw / thrust
```

No inference-time teacher, planner, shield, ensemble, waypoint controller, or
upper-level controller is added.

## Local Evidence

loop119 was interrupted after saving the 45M checkpoint. loop120 recovered from
that checkpoint and added a 15M continuation, giving an effective 60M read of
the v49 hidden512 baseline.

Hard eval on `validation_unseen` did not improve:

| Checkpoint | Success | Mean gates | Crash | Mean successful time |
| --- | ---: | ---: | ---: | ---: |
| loop120 recovery 5M | 15% | 1.50 | 85% | 6.741s |
| loop120 recovery 10M | 14% | 1.46 | 86% | 6.499s |
| loop120 final | 13% | 1.41 | 87% | 6.529s |

The old frontier remains around `21%` success and `1.66` mean gates. v49 did
not catastrophically lose all gate progress, so hidden512 should not be
abandoned. But the trend worsened across the recovery milestones, so the same
v49 schedule should not be blindly continued to 90M/120M.

W&B/PPO diagnostics point to weak policy movement late in the run:

- `losses/approx_kl`: about `0.000002`;
- `losses/clipfrac`: `0.0`;
- `losses/policy_loss`: near zero;
- `losses/entropy`: rising to about `5.38`;
- `train/reward`: down;
- `race/passed_gate_rate` and `race/finished_rate`: flat;
- `race/crashed_rate`: flat/high.

That is a more specific diagnosis than "512 is bad": the larger network was
trained with a low `5e-5` learning rate and annealing inside each continuation
chunk, and by the end it was barely changing policy behavior.

## V50 Hypothesis

```text
v50_hidden512_update_pressure_conversion_from_loop110_3m
```

The next hidden512-family test should keep the architecture family but change
PPO training numbers so updates remain active:

- start again from loop110/v39 3M, not loop120 final;
- block-copy warm-start hidden_dim `256 -> 512`;
- keep v5 observation;
- keep v39 reward numbers;
- keep train and hard eval on unchanged `config/level3.toml`;
- keep retention off;
- increase update pressure and reduce entropy pressure.

## V50 Training Numbers

Changed training numbers versus v49:

| Parameter | v49 | v50 |
| --- | ---: | ---: |
| `learning_rate` | `5e-5` | `1e-4` |
| `anneal_lr` | `True` | `False` |
| `update_epochs` | `5` | `8` |
| `clip_coef` | `0.26` | `0.30` |
| `ent_coef` | `0.02` | `0.005` |
| `vf_coef` | `0.7` | `0.5` |
| `target_kl` | `0.03` | `0.05` |
| `train_timesteps` | `60M` | `30M` screen |

Unchanged:

- `hidden_dim=512`;
- `policy_arch=mlp_2x_tanh`;
- v5 observation layout;
- v39 gate-acquisition reward numbers;
- `num_envs=256`, `num_steps=128`;
- `config/level3.toml` for training and hard eval.

## Expected Signal

v50 is useful if W&B shows non-degenerate updates and evaluator progress:

- `approx_kl` rises above the near-zero loop120 level without repeated KL stop;
- `clipfrac` becomes non-zero but not saturated;
- entropy stops drifting upward;
- passed-gate or finished metrics improve;
- hard-eval mean gates recovers toward `1.55+`;
- success recovers toward `18%+` without crash/tilt blow-up.

v50 is not useful if higher update pressure only increases crash/tilt or still
fails to move evaluator metrics.

## Decision Rule After V50

- If any checkpoint is near the old frontier or shows better mean gates plus
  healthier W&B conversion, continue v50 toward 60M with milestone selection.
- If v50 stays below `16%` success and below `1.50` mean gates, stop PPO-number
  tuning and launch the required hidden512 observation, memory, or curriculum
  follow-up.
- If v50 has update movement but unstable crash/tilt, choose a hidden512
  stability lane rather than pure reward scaling.

Do not modify `config/level3.toml` under any outcome.
