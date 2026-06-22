# Main-Agent Decision After loop051

Date: 2026-06-21

## Trial

- Trial:
  `level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m`

Best loop051 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m/level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m_step_015000000.ckpt`

Hard-eval metrics:

- Success rate: `0.10`
- Mean successful time: `5.38s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.15`
- Mean action delta: `0.33588467248861`
- Mean max commanded tilt: `61.32233837612206deg`
- Commanded tilt over-limit fraction: `0.48560821747359917`

Global best remains loop020:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`,
crash `0.85`, and mean gates `1.45`.

The audited remote safer final checkpoint also ties that frontier with smoother
controls:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

with success `0.15`, mean successful time `6.3066666666666675s`,
crash `0.85`, mean gates `1.45`, and lower action/tilt metrics than loop020.

## Subagent Findings

- `evaluator_metrics` recommended `hold_for_more_analysis`.
  loop051 should not be promoted or matured because it regressed versus loop020,
  loop050, and the remote safer anchor.
- `wandb_ppo_diagnostics` recommended `hold_for_more_analysis`.
  Training-side reward moved, but gate/finish conversion stayed flat. PPO was
  not explosively unstable, but the update signal did not convert into
  evaluator progress.
- `structure_research_synthesis` recommended
  `launch_named_structural_lane`.
  It found loop051 falsified the gate-acquisition retune and recommended
  returning to the remote safer nominal reward scale as an explicit lane.

## Main-Agent Decision

Selected decision:

`launch_named_structural_lane`

Do not continue loop051 and do not mature this exact branch.

Launch a bounded structural lane that returns to the remote ordinary safer
nominal reward scale on `level3_dr.toml`, starting from the audited remote
safer final checkpoint.

## Rationale

loop051 failed its promotion criteria:

- success fell from loop050 `0.15` to `0.10`;
- crash worsened from `0.85` to `0.90`;
- mean gates stayed below loop020 and the remote safer anchor;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` stayed
  flat.

The completion-backloaded branch has now had two negative pieces of evidence:

- loop050 preserved success but lost gate progress;
- loop051 tried to recover gate acquisition and instead lost success/crash.

The strongest current non-loop020 anchor is still the remote ordinary safer
final checkpoint. It tied the frontier in hard eval and is smoother. The next
test should use the reward profile that produced that anchor, not the later
completion-heavy or high-crash variants.

## Approved Next Experiment

Name:

`v5_remote_safer_anchor_nominal_reward_dr_30m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `legacy_staged`
- Controller:
  `action_rp_limit_deg=90`, `action_lowpass_alpha=1.0`
- PPO/training:
  `learning_rate=5e-5`, `hidden_dim=256`, `n_obs=2`
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Reward/training numbers:

- `progress_coef = 0.0`
- `gate_stage_coef = 10.0`
- `gate_axis_coef = 12.0`
- `near_gate_coef = 0.0`
- `gate_bonus = 90.0`
- `gate_front_bonus = 0.0`
- `gate_plane_bonus = 0.0`
- `gate_back_bonus = 12.0`
- `finish_bonus = 160.0`
- `missed_gate_penalty = 0.0`
- `gate_frame_pressure_coef = 0.0`
- `wrong_side_penalty = 8.0`
- `crash_penalty = 100.0`
- `obstacle_coef = 8.0`
- `obstacle_margin = 0.40`
- `obstacle_clearance_coef = 6.0`
- `timeout_penalty = 80.0`
- `time_penalty = 0.03`
- `act_coef = 0.03`
- `d_act_th_coef = 0.10`
- `d_act_xy_coef = 0.10`
- `cmd_tilt_coef = 1.0`
- `rpy_coef = 1.0`
- `tilt_limit_deg = 40.0`
- `tilt_excess_coef = 15.0`

This is a structural lane because `obstacle_clearance_coef` is enabled and the
reward scale is intentionally reset to the remote nominal safer profile.

## Required Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --override-state-hold \
  --proposal-name v5_remote_safer_anchor_nominal_reward_dr_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_051_v5_remote_safer_anchor_gate_acquisition_retune_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop051_launch_remote_nominal_reward_dr_lane.md \
  --param learning_rate=0.00005 \
  --param gamma=0.99 \
  --param gae_lambda=0.95 \
  --param update_epochs=5 \
  --param num_minibatches=8 \
  --param ent_coef=0.02 \
  --param target_kl=0.03 \
  --param hidden_dim=256 \
  --param n_obs=2 \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=10.0 \
  --param gate_axis_coef=12.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=90.0 \
  --param gate_front_bonus=0.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=12.0 \
  --param finish_bonus=160.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=8.0 \
  --param crash_penalty=100.0 \
  --param obstacle_coef=8.0 \
  --param obstacle_margin=0.40 \
  --param obstacle_clearance_coef=6.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.03 \
  --param act_coef=0.03 \
  --param d_act_th_coef=0.10 \
  --param d_act_xy_coef=0.10 \
  --param cmd_tilt_coef=1.0 \
  --param rpy_coef=1.0 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=15.0
```

If dry-run passes, run the same command without `--dry-run`.

## Promotion And Rollback

Promote if hard eval on `config/level3_dr.toml` beats loop020:

- success rate `> 0.15`; or
- mean gates `> 1.45`; or
- success `0.15` with mean gates at least `1.45`, crash no worse than `0.85`,
  and materially better action/tilt stability than loop020.

Hold or reject if:

- all checkpoints stay `<= 0.10` success;
- mean gates stay below `1.20`;
- crash rises above `0.90`;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` remain
  flat while reward rises.

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then repeat the three-review decision gate before any further training.
