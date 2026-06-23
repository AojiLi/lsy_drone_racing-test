# Level3 V43 Success-Trajectory Imitation Warmstart Plan

Status: structural research packet for the next Level3 PPO support lane.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization
  changes.

Deployment remains a single end-to-end PPO Actor:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is part of this packet.

## Local Evidence

v40 tested true GRU/v10 from scratch and failed with `0%` success and `0.0`
mean gates. v41 then passed the wiring audit, ruling out the main suspected
implementation bugs. v42 added training-only gate-phase reset curriculum and
still failed:

| Checkpoint | Success | Mean Gates | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| 1M | 0% | 0.00 | 58% | 42% |
| 2M | 0% | 0.00 | 65% | 35% |
| 3M | 0% | 0.01 | 60% | 40% |
| 4M | 0% | 0.01 | 54% | 46% |
| 5M | 0% | 0.00 | 64% | 36% |
| 8M | 0% | 0.00 | 61% | 39% |
| 9M | 0% | 0.00 | 57% | 43% |
| final | 0% | 0.00 | 62% | 38% |

The corrected global best remains loop107 1M:

- `21%` success;
- `1.66` mean gates;
- `79%` crash;
- `7.578s` mean successful time.

The issue is not that the Level3 evaluator changed and not that v10/GRU wiring
is obviously broken. The current failure is that true GRU/v10 from scratch does
not acquire normal-start gate 0 behavior.

## Existing Support And Gap

The repository already has partial imitation-style infrastructure:

- `scripts/build_v27_retention_dataset.py` can collect successful teacher
  rollouts and store student-layout observations plus teacher action
  distributions;
- `train_CleanRL_ppo_level3.py` can apply dataset retention KL for MLP policies;
- `train_CleanRL_ppo_level3.py` can apply online teacher retention for the
  residual-GRU v5 lane.

The missing piece for v43 is true GRU/v10 behavior-cloning warm start support:

- sequence-aware dataset batches grouped by episode;
- hidden-state reset at episode boundaries;
- supervised KL/MSE from teacher action distribution to the
  `recurrent_actor_gru256` Actor;
- checkpoint metadata for
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`;
- a preflight proving load/save parity and nontrivial action movement before
  PPO fine-tuning.

## Hypothesis

```text
v43_success_trajectory_imitation_warmstart_gru_v10
```

If from-scratch GRU/v10 cannot discover first-gate acquisition, initialize it
from successful train-pool trajectories produced by a known v5-family PPO
teacher. Then fine-tune the same single end-to-end GRU/v10 Actor with PPO on
unchanged `config/level3.toml`.

The teacher is used only during training/pretraining. The deployed controller
remains the PPO Actor; no teacher, planner, shield, or fallback controller is
used at inference.

## Required Preflight

Before launching PPO training, v43 must pass:

1. Build or audit a v10 student-observation success-trajectory dataset from
   successful train-pool teacher rollouts, excluding dev, validation, and final
   seed ranges.
2. Train a GRU/v10 BC warmstart checkpoint from the dataset.
3. Verify checkpoint metadata:
   `policy_arch=recurrent_actor_gru256`,
   `observation_layout=level3_gate_corridor_aperture_margin_2obs_local_history_v10`,
   `recurrent_hidden_dim=256`, and same action envelope as PPO.
4. Verify zero-update load/save parity.
5. Verify the supervised pretraining reduces action MSE or KL versus teacher
   distributions and produces nontrivial deterministic action authority.
6. Hard-eval the BC checkpoint alone on unchanged `config/level3.toml` as a
   diagnostic, but do not require it to meet the final target before PPO.

## First PPO Screen After Preflight

If preflight passes, launch a bounded v43 PPO fine-tune:

- initial checkpoint: v43 BC warmstart checkpoint;
- train config: unchanged `config/level3.toml`;
- hard eval config: unchanged `config/level3.toml`;
- policy: `recurrent_actor_gru256`;
- observation:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`;
- horizon: `5M` to `10M` first screen;
- checkpoint interval: `1M`;
- hard-eval milestones: `1M, 2M, 3M, 4M, 5M` and optionally `8M, 10M`;
- W&B logging required.

Promotion gate:

- nonzero hard-eval success; or
- mean gates above `0.5`; or
- clear first-gate conversion beyond v42's `0.01` mean gates; or
- a BC checkpoint that already shows meaningful normal-start gate progress.

Reject if hard eval remains `0%` success and below `0.5` mean gates after the
PPO screen, or if W&B imitation metrics look good but normal-start evaluator
progress does not move.
