# V54 Reference Tracker Long-Training Preparation

Created: 2026-06-25

Lane: `v54_reference_trajectory_tracker_ppo`

Target config remains unchanged: `config/level3.toml`.

## Goal

Prepare the v54 native PPO reference tracker for a later manual long-training
run as the low-level controller:

```text
upper planner/reference generator
  -> v54 tracker observation
  -> PPO tracker
  -> roll / pitch / yaw / thrust
```

The long-training command is not allowed unless the bounded prep proves the
setup is credible.

Required promotion gate for this prep:

- all smoke actions finite;
- no NaN/inf symptoms in training or smoke;
- checkpoint-backed smoke;
- nonzero first-gate progress on a majority of Level3 smoke seeds;
- at least one Level3 smoke seed actually passes gate 0;
- early termination clearly better than the previous v54 preflight;
- `config/level3.toml` unchanged.

## Builder / Checker Gate

The builder changed v54 training and smoke semantics only:

- exposed `ReferenceTrackerReward` coefficients as trainer CLI arguments;
- stored reward coefficients in checkpoint metadata;
- allowed `ReferenceTrackerEnv` to receive explicit reward coefficients;
- made the controller read `rp_limit_deg` from checkpoint metadata, preserving
  train/inference action-scale parity;
- made smoke readiness strict: checkpoint-backed, finite, majority first-gate
  progress, and at least one seed with `max_gate_index > 0`.

Read-only checker result: `ALL GREEN`.

Checker verified:

- `git diff --check` passed;
- Python compile passed;
- `ruff check` passed;
- `config/level3.toml` was unchanged;
- trainer and smoke `--help` were healthy;
- `--require-long-training-ready` exits nonzero when readiness fails.

## Baseline Smoke Before Tuning

Checkpoint:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_curriculum_preflight/v54_reference_tracker_curriculum_gate_aperture.ckpt`

Command used `config/level3.toml`, seeds `101-120`, and `220` max steps.

Summary:

| metric | value |
| --- | ---: |
| finite actions | 20 / 20 |
| nonzero first-gate progress | 13 / 20 |
| seeds passing gate 0 | 0 / 20 |
| terminated before max steps | 20 / 20 |
| mean steps | 26.3 |
| median steps | 22.5 |
| mean first-gate axis gain | 0.410 |

The old loose smoke script reported this as ready because it only required any
first-gate progress. Under the stricter goal gate, this baseline is not ready:
no seed passed gate 0.

## Diagnostic Training 1

Hypothesis: gentle continuation on `gate_aperture` with lower learning rate and
entropy can stabilize the current tracker without changing reward semantics.

W&B:

[v54_tracker_longprep_gate_aperture_lr1e4_32k_20260625](https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v54_tracker_longprep_gate_aperture_lr1e4_32k_20260625)

Command shape:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3.toml \
  --task gate_aperture \
  --seed 544 \
  --total-timesteps 32768 \
  --learning-rate 1e-4 \
  --ent-coef 0.003 \
  --max-episode-steps 600 \
  --initial-model-path lsy_drone_racing/control/checkpoints/v54_reference_tracker_curriculum_preflight/v54_reference_tracker_curriculum_gate_aperture.ckpt \
  --model-path lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt \
  --checkpoint-interval 8192 \
  --wandb-enabled
```

Checkpoint:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt`

Final global step: `57344`.

Strict smoke on `config/level3.toml`, seeds `101-120`, `300` max steps:

| metric | value |
| --- | ---: |
| all finite | true |
| checkpoint-backed | true |
| nonzero first-gate progress | 14 / 20 |
| seeds passing gate 0 | 0 / 20 |
| early termination `<50` steps | 18 / 20 |
| mean steps | 30.2 |
| mean first-gate axis gain | 0.412 |
| long-training gate | false |

Readiness failure:

```text
no_seed_passed_gate_0
```

## Diagnostic Training 2

Hypothesis: a more stable deployed action envelope plus stronger centering,
smoothness, and crash pressure can reduce early termination and convert first
gate progress into a real gate-0 pass.

W&B:

[v54_tracker_longprep_level3_stability_rp35_32k_20260625](https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v54_tracker_longprep_level3_stability_rp35_32k_20260625)

Command shape:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3.toml \
  --task level3 \
  --seed 545 \
  --total-timesteps 32768 \
  --learning-rate 7e-5 \
  --ent-coef 0.001 \
  --max-episode-steps 700 \
  --rp-limit-deg 35 \
  --gate-center-coef 2.0 \
  --action-coef 0.08 \
  --action-delta-coef 0.12 \
  --progress-bonus 0.6 \
  --crash-penalty 35.0 \
  --initial-model-path lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt \
  --model-path lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_level3_stability_rp35_32k.ckpt \
  --checkpoint-interval 8192 \
  --wandb-enabled
```

Checkpoint:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_level3_stability_rp35_32k.ckpt`

Final global step: `90112`.

Strict smoke on `config/level3.toml`, seeds `101-120`, `300` max steps:

| metric | value |
| --- | ---: |
| all finite | true |
| checkpoint-backed | true |
| nonzero first-gate progress | 13 / 20 |
| seeds passing gate 0 | 0 / 20 |
| early termination `<50` steps | 18 / 20 |
| mean steps | 26.75 |
| mean first-gate axis gain | 0.411 |
| long-training gate | false |

Readiness failure:

```text
no_seed_passed_gate_0
```

## Decision

Long training is held.

Do not start the overnight/manual long-training run from either diagnostic
checkpoint. The best diagnostic checkpoint is:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt`

It is "best" only in the narrow diagnostic sense: it had 14 / 20 seeds with
nonzero first-gate progress and slightly longer mean survival than the rp35
follow-up. It still failed the decisive gate because 0 / 20 seeds passed gate 0.

## Interpretation

The v54 pipeline is technically healthy:

- actions are finite;
- checkpoint loading works;
- W&B logging works;
- trainer continuation works;
- strict smoke now prevents false promotion.

But the behavior is not ready:

- the tracker can move roughly toward gate 0;
- it cannot consistently center and pass through gate 0;
- early termination remains very high;
- reducing roll/pitch envelope to `35deg` did not improve the gate-pass result.

The missing piece is not simply more long-horizon steps. The next v54 structural
fix should teach gate-aperture completion directly before long training:

- add a dedicated gate-aperture reset/curriculum that starts near pre-gate,
  align, cross, and recover phases instead of relying on full Level3 starts;
- add explicit phase-completion or gate-plane crossing bonuses inside the
  tracker task;
- hard-check mini-task gate crossing before Level3 smoke promotion;
- only then reconsider a 10M/30M long-training command.

## Artifacts

Ignored generated artifacts:

- `lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt`
- `lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_level3_stability_rp35_32k.ckpt`
- smoke JSON reports under `experiments/level3_ppo_loop/analysis/*.json`
- W&B run directories under `wandb/`

These were intentionally not committed.
