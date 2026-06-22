# Main-Agent Decision After loop048

Date: 2026-06-21

## Trial

- Trial id:
  `level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m`

Best loop048 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_final.ckpt`

Hard-eval metrics:

- Success rate: `0.15`
- Mean successful time: `6.406666666666666s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.25`
- Target met: `false`

Global best remains loop020:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`,
crash `0.85`, and mean gates `1.45`.

## Subagent Findings

- `evaluator_metrics` recommended `change_reward_or_training_numbers`.
  loop048 tied loop047 on success, crash, timeout, and mean gates, while
  staying below loop020 on mean gates and being slightly slower.
- `wandb_ppo_diagnostics` recommended
  `change_reward_or_training_numbers`. W&B reward and safety-looking shaped
  terms did not convert into hard-eval gate acquisition or finishes. PPO was
  stable, but late updates were weak and pass/finish signals stayed flat.
- `structure_research_synthesis` recommended
  `launch_named_structural_lane`. It found enough evidence to stop loop047/048
  same-hypothesis maturation and proposed isolating whether loop047/048's
  damping/safety changes caused the loss of loop020 gate progress.

## Main-Agent Decision

Selected decision:

`launch_named_structural_lane`

## Rationale

The loop047/048 same-hypothesis maturation should stop.

Reasons:

- The 60M-style continuation produced no hard-eval improvement over loop047.
- It remained below loop020 on mean gates: `1.25` vs `1.45`.
- Early and middle milestones were weak: `10M`, `15M`, and `20M` had `0.00`
  success; `25M` had only `0.10`.
- W&B pass/finish/gate-plane conversion stayed flat.
- Continuing unchanged toward 90M would spend budget on a plateaued lane.

The next useful experiment should be a clean isolation lane, not another generic
reward retune. loop047/048 changed two things relative to loop020:

- moderate PPO pressure; and
- controller/safety damping.

The damping reduced command tilt saturation, but mean gates fell. The next lane
therefore keeps the moderate PPO pressure and restores loop020-style controller
authority/safety values to test whether the damping caused the gate-progress
regression.

## Structural Lane

Lane name:

`v5_loop020_moderate_ppo_no_damping_isolation_30m`

Hypothesis:

loop047/048's mild low-pass and stronger safety/smoothness penalties reduced
command saturation but also reduced gate progress. Starting again from loop020,
moderate PPO update pressure without the extra damping may preserve loop020's
gate frontier while allowing additional learning.

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Scope:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure:
  `legacy_staged`
- Reward numbers:
  keep loop020 completion-backloaded values unchanged.
- PPO/training:
  keep loop047 moderate PPO pressure.
- Controller/safety:
  restore loop020 authority and damping values.
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

## Parameters

Use these explicit values to avoid automatic reward proposals:

PPO/training:

- `learning_rate=0.0002`
- `update_epochs=6`
- `ent_coef=0.01`
- `target_kl=0.04`

Controller/safety restored toward loop020:

- `action_lowpass_alpha=1.0`
- `action_rp_limit_deg=90`
- `act_coef=0.012`
- `d_act_th_coef=0.055`
- `d_act_xy_coef=0.055`
- `cmd_tilt_coef=0.75`
- `rpy_coef=0.65`
- `tilt_limit_deg=42`
- `tilt_excess_coef=10`

Reward/event values pinned to loop020 family:

- `reward_structure=legacy_staged`
- `progress_coef=0.0`
- `gate_stage_coef=9`
- `gate_axis_coef=22`
- `near_gate_coef=0.0`
- `gate_bonus=180`
- `gate_front_bonus=22`
- `gate_plane_bonus=0.0`
- `gate_back_bonus=95`
- `finish_bonus=300`
- `missed_gate_penalty=0.0`
- `gate_frame_pressure_coef=0.0`
- `wrong_side_penalty=14`
- `crash_penalty=50`
- `obstacle_coef=4.5`
- `obstacle_margin=0.3`
- `obstacle_clearance_coef=0.0`
- `timeout_penalty=80`
- `time_penalty=0.005`

## Promotion And Rollback

Promote if any checkpoint beats loop020 on at least one main frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45` and crash no worse than
  `0.85`; or
- success `0.15` with materially lower crash and no gate regression.

Reject this lane if:

- no checkpoint beats loop020 on success or mean gates;
- all checkpoints stay `<=0.10` success;
- all checkpoints stay below `1.25` mean gates;
- late checkpoints collapse to `0.00` success or `1.00` crash;
- command tilt rises materially above loop020 without hard-eval progress;
- W&B reward improves while pass/finish/gate-plane conversion stays flat.

If this isolation lane fails, do not continue local v5 PPO/controller variants
unchanged. Hold for a deeper observation/controller/reward-structure decision
packet.

## Required Dry-Run Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_loop020_moderate_ppo_no_damping_isolation_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop048_launch_v5_no_damping_isolation.md \
  --param learning_rate=0.0002 \
  --param update_epochs=6 \
  --param ent_coef=0.01 \
  --param target_kl=0.04 \
  --param action_rp_limit_deg=90 \
  --param action_lowpass_alpha=1.0 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=9 \
  --param gate_axis_coef=22 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=180 \
  --param gate_front_bonus=22 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=95 \
  --param finish_bonus=300 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=14 \
  --param crash_penalty=50 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80 \
  --param time_penalty=0.005 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42 \
  --param tilt_excess_coef=10
```

If the dry-run is clean, run the same command without `--dry-run`.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not modify `notebooks/train_level3_ppo.ipynb`.
- Do not treat W&B reward as acceptance.
- Do not resume from loop048 final for this lane.
