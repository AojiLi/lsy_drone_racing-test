# V43 Success-Trajectory BC Warmstart Preflight

Date: 2026-06-23

Lane:
`v43_success_trajectory_imitation_warmstart_gru_v10`

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- `config/level3.toml` geometry, gate layout, obstacle layout, and
  randomization were not modified.
- The deployed controller remains a single PPO Actor producing
  roll/pitch/yaw/thrust.
- The teacher and BC data are training/pretraining artifacts only; there is no
  MPC, planner, rule controller, inference-time shield, fallback controller, or
  upper-level controller.

## Dataset

Command:

```bash
pixi run -e gpu python scripts/build_v27_retention_dataset.py \
  --config level3.toml \
  --teacher-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --student-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_final.ckpt \
  --out experiments/level3_ppo_loop/retention_datasets/v43_loop110_train_pool_success_v5_teacher_v10_student.npz \
  --inference-module ppo_level3_inference \
  --seed-start 2001 \
  --max-seeds 500 \
  --target-successes 8 \
  --min-successes 2 \
  --max-samples 20000 \
  --exclude-seed-ranges 1-20,101-200,1001-1200
```

Result:

- config: `level3.toml`
- teacher: loop110/v39 3M feed-forward checkpoint
- teacher observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- student observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- excluded seed ranges: `1-20,101-200,1001-1200`
- attempted seeds: 2001-2049
- success seeds: `2001, 2010, 2021, 2029, 2042, 2045, 2047, 2049`
- samples: 2559
- sequences: 8

Generated dataset:

`experiments/level3_ppo_loop/retention_datasets/v43_loop110_train_pool_success_v5_teacher_v10_student.npz`

This `.npz` is intentionally ignored by git.

## BC Training

Command:

```bash
pixi run -e gpu python scripts/train_level3_v43_bc_warmstart.py \
  --dataset experiments/level3_ppo_loop/retention_datasets/v43_loop110_train_pool_success_v5_teacher_v10_student.npz \
  --out lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt \
  --metrics-out experiments/level3_ppo_loop/parity/2026-06-23_v43_success_trajectory_bc_warmstart_metrics.json \
  --sequence-len 64 \
  --batch-size 64 \
  --steps 2000 \
  --learning-rate 3e-4 \
  --seed 43
```

Result:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt`
- policy arch: `recurrent_actor_gru256`
- observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- obs dim: 91
- sequence length: 64
- initial teacher action MSE: 0.2658945322
- final teacher action MSE: 0.0015148986
- initial teacher KL: 104.3998184204
- final teacher KL: 22.9460887909
- initial teacher agreement: 0.2694091797
- final teacher agreement: 0.9910888672

The supervised action-learning preflight passed: the GRU/v10 student learned
the teacher action distribution on successful train-pool trajectories.

## BC-Only Hard Eval

Command:

```bash
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3.toml \
  --seed-file experiments/level3_ppo_loop/seed_manifests/validation_unseen_101_200.txt \
  --seed-split-name validation_unseen \
  --inference-module ppo_level3_inference \
  --failure-taxonomy \
  --out-prefix experiments/level3_ppo_loop/eval/v43_bc_warmstart_validation_unseen \
  lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt
```

Result on unchanged `config/level3.toml`, validation_unseen seeds 101-200:

- success: 0/100
- success rate: 0.0
- mean gates: 0.15
- crash rate: 0.99
- timeout rate: 0.01
- failures by target gate: gate0 88, gate1 10, gate2 2, gate3 0
- mean successful time: NaN
- mean max tilt: 31.76 deg
- mean max commanded tilt: 50.34 deg

Generated evaluator CSVs:

- `experiments/level3_ppo_loop/eval/v43_bc_warmstart_validation_unseen_summary.csv`
- `experiments/level3_ppo_loop/eval/v43_bc_warmstart_validation_unseen_episodes.csv`

These CSVs are generated artifacts and are intentionally not committed.

## Interpretation

The BC checkpoint is not a deployable controller: it has 0% validation success
and 99% crash.

However, it is a meaningful preflight signal for PPO fine-tuning. v40 had
0.00 mean gates and v42 reached only 0.01 mean gates; the BC checkpoint reaches
0.15 mean gates, with 12 validation seeds passing at least gate 0. This meets
the v43 diagnostic rule for clear first-gate conversion beyond v42, but not the
rule for success.

Next action: launch one bounded v43 PPO fine-tune screen from this BC
checkpoint, with W&B logging, 1M milestone hard eval, and post-run analysis
before any next chunk.
