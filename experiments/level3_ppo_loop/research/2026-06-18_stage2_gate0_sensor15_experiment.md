# Level3 PPO Stage 2 Experiment: Gate0 Sensor-Range Staging Probe

## Scope

This packet approves one bounded Stage 2 training experiment. It is not a
reward-only Stage 1 continuation.

The experiment changes only the training config used by the train subprocess.
The hard evaluator remains `config/level3_dr.toml`.

Approved training config:

```text
config/level3_dr_stage2_gate0_sensor15.toml
```

Approved hard evaluation config:

```text
config/level3_dr.toml
```

## Hypothesis

The Stage 2 geometry diagnostic showed that gate 0 is visible at reset in only
`17%` of sampled Level3 resets with `sensor_range=0.7`. The policy usually
starts from nominal object positions, while the actual perturbed gate position
differs by about `0.108m` median XY and up to `0.175m` at p95 in the sampled
distribution. Early crashes remain concentrated around target gates `0` and
`1`.

Hypothesis:

- If early learning is blocked by first-gate observability and nominal-vs-actual
  geometry mismatch, then training with a larger sensor range should improve
  gate acquisition.
- The experiment should improve hard-eval `success_rate`, `mean_gates`, or
  crash taxonomy on the original `level3_dr.toml`.

## Exact Change

Create `config/level3_dr_stage2_gate0_sensor15.toml` from
`config/level3_dr.toml` with only this semantic training change:

```toml
[env]
sensor_range = 1.5
```

Everything else remains the same:

- PPO algorithm and hyperparameters unchanged.
- Observation layout unchanged.
- Network unchanged.
- Reward channels and coefficients unchanged from the current global incumbent
  baseline reward profile.
- Full Level3 track randomization remains enabled.
- Gate/obstacle perturbation randomization remains enabled.
- Train-only thrust, latency, response, observation-noise, mass, and inertia DR
  remain enabled.
- Evaluation remains on `level3_dr.toml` with `sensor_range=0.7`.

## Training Parameters

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Reward/PPO parameters:

- Use the `level3_loop_001_baseline` reward and PPO parameters.
- Disabled reward channels stay disabled:
  `progress_coef=0`, `near_gate_coef=0`, `gate_plane_bonus=0`,
  `missed_gate_penalty=0`, `obstacle_clearance_coef=0`.

Run shape:

- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`
- W&B entity: `aojili77-technical-university-of-munich`
- Proposed run suffix: `stage2_gate0_sensor15_probe`

## Command

Use one train/eval chunk:

```text
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --config level3_dr_stage2_gate0_sensor15.toml \
  --eval-config level3_dr.toml \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name stage2_gate0_sensor15_probe \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt \
  --research-packet experiments/level3_ppo_loop/research/2026-06-18_stage2_parity_geometry_decision.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/research/2026-06-18_stage2_gate0_sensor15_experiment.md \
  --param gate_stage_coef=10.0 \
  --param gate_axis_coef=20.0 \
  --param gate_bonus=180.0 \
  --param gate_front_bonus=4.0 \
  --param gate_back_bonus=30.0 \
  --param finish_bonus=160.0 \
  --param wrong_side_penalty=6.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=5.0 \
  --param obstacle_margin=0.2 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.03 \
  --param act_coef=0.015 \
  --param d_act_th_coef=0.07 \
  --param d_act_xy_coef=0.07 \
  --param cmd_tilt_coef=0.7 \
  --param rpy_coef=0.7 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=12.0
```

After the chunk finishes, run the required W&B-backed analyzer:

```text
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

## Acceptance And Rollback

Accept this staging direction only if hard evaluation on original
`level3_dr.toml` shows at least one of:

- `success_rate > 0.0`;
- `mean_gates > 0.85`;
- `crash_rate < 1.0`;
- crash taxonomy shows fewer target-gate `0`/`1` crashes with a linked
  improvement in evaluator gates.

Rollback/hold if:

- hard-eval `success_rate == 0.0` and `mean_gates <= 0.85`;
- W&B gate/finish curves do not improve;
- command tilt or crash behavior worsens without evaluator progress.

If rollback/hold triggers, do not keep raising `sensor_range`. Move to an
observation/event parity packet instead.
