# Main-Agent Decision After loop050

Date: 2026-06-21

## Trial

- Trial:
  `level3_loop_050_v5_remote_safer_anchor_completion_dr_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m`

Best loop050 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m_step_020000000.ckpt`

Hard-eval metrics:

- Success rate: `0.15`
- Mean successful time: `6.54s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.20`
- Mean action delta: `0.3025737051921631`
- Mean max commanded tilt: `60.02028896795305deg`
- Commanded tilt over-limit fraction: `0.4578592385203798`

Global best remains loop020:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`,
crash `0.85`, and mean gates `1.45`.

## Subagent Findings

- `evaluator_metrics` recommended `continue_same_hypothesis`.
  It noted loop050 tied loop020 on success/crash and preserved smoother
  action/tilt behavior, but also acknowledged mean gates regressed from `1.45`
  to `1.20`.
- `wandb_ppo_diagnostics` recommended `change_reward_or_training_numbers`.
  It found weak reward conversion: `train/reward` rose, but `train/total_reward`
  fell and W&B pass/finish/gate-plane signals did not improve. PPO appeared
  stable but conservative: tail KL around `0.0002`, `clipfrac=0`, flat policy
  loss, and rising entropy.
- `structure_research_synthesis` recommended
  `change_reward_or_training_numbers`.
  It concluded that unchanged maturation is not clean because the later
  checkpoints decayed and mean gates stayed below the loop020/remote-anchor
  frontier.

## Main-Agent Decision

Selected decision:

`change_reward_or_training_numbers`

Do not continue loop050 unchanged.

Run a bounded gate-acquisition retune from the loop050 20M checkpoint. Keep the
v5 local observation layout, controller, reward structure, PPO architecture,
and Level3 track fixed. Shift reward numbers away from pure
completion-backloading and toward gate acquisition/pass conversion.

## Rationale

loop050 partially worked: it recovered from loop049 to `0.15` success and
`0.85` crash while staying smoother than loop020. But it did not beat loop020
and it lost gate progress:

- loop020 mean gates: `1.45`
- remote safer anchor mean gates: `1.45`
- loop050 best mean gates: `1.20`

The 20M checkpoint is the only useful continuation anchor from loop050. Later
checkpoints decayed to `0.10` success and `1.00-1.05` mean gates.

The next move should test whether a gate-acquisition reward rebalance can
recover mean gates without losing loop050's smoother control profile.

## Approved Next Experiment

Name:

`v5_remote_safer_anchor_gate_acquisition_retune_20m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m_step_020000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `legacy_staged`
- Controller:
  `action_rp_limit_deg=90`, `action_lowpass_alpha=1.0`
- PPO/training:
  keep loop050 values, including `learning_rate=5e-5`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Reward/training number changes versus loop050:

- `gate_stage_coef: 9 -> 13`
- `gate_axis_coef: 22 -> 24`
- `gate_front_bonus: 22 -> 5`
- `gate_bonus: 180 -> 200`
- `gate_back_bonus: 95 -> 35`
- `finish_bonus: 300 -> 175`
- `time_penalty: 0.005 -> 0.02`

All other reward/controller/PPO numbers stay explicit and unchanged from
loop050 unless listed in the command.

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
  --proposal-name v5_remote_safer_anchor_gate_acquisition_retune_20m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 20000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m_step_020000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_050_v5_remote_safer_anchor_completion_dr_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_safer_anchor_completion_dr_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop050_gate_acquisition_retune_from_remote_safer_anchor.md \
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
  --param gate_stage_coef=13.0 \
  --param gate_axis_coef=24.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=200.0 \
  --param gate_front_bonus=5.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=35.0 \
  --param finish_bonus=175.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.02 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=10.0
```

If dry-run passes, run the same command without `--dry-run`.

## Promotion And Rollback

Promote if hard eval on `config/level3_dr.toml` beats loop020:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45`, crash no worse than `0.85`,
  and no loss of the smoother action/tilt profile.

Hold or reject if:

- all checkpoints stay `<=0.10` success;
- mean gates stay below `1.20`;
- crash rises above `0.85`;
- late checkpoints collapse after an early promising checkpoint;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` remain
  flat while reward rises.

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then repeat the three-review decision gate before any further training.
