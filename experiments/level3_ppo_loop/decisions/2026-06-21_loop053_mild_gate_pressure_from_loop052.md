# Main-Agent Decision After loop053

Date: 2026-06-21

## Trial

- Trial:
  `level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m`

Best loop053 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m/level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m_step_025000000.ckpt`

Hard-eval metrics:

- Success rate: `0.20`
- Mean successful time: `6.95s`
- Crash rate: `0.80`
- Timeout rate: `0.00`
- Mean gates: `1.15`
- Mean action delta: `0.2865206500568445`
- Mean max commanded tilt: `53.782690537274334deg`
- Commanded tilt over-limit fraction: `0.26511578801440955`

Global best remains loop052:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

with success `0.20`, mean successful time `6.975s`, crash `0.80`,
and mean gates `1.40`.

## Subagent Findings

- `evaluator_metrics` recommended `hold_for_more_analysis`.
  The 60M-style maturation did not improve success or gates and does not justify
  blind continuation to 90M.
- `wandb_ppo_diagnostics` recommended `launch_named_structural_lane`.
  It found reward moved but gate/finish conversion stayed flat. PPO looked
  under-updated rather than unstable.
- `structure_research_synthesis` recommended
  `change_reward_or_training_numbers`.
  It found loop053 falsified further same-lane maturation as-is and advised
  returning to loop052 final with an explicit reward/training-number change.

## Main-Agent Decision

Selected decision:

`change_reward_or_training_numbers`

Do not continue loop053 and do not mature the unchanged nominal reward lane to
90M. Return to the loop052 final checkpoint and run one bounded 20M screen with
explicit reward-number changes.

## Rationale

loop052 proved that the remote nominal reward lane can beat the old frontier,
but loop053 showed that simply adding another 30M with identical parameters
does not convert:

- success stayed at `0.20`;
- mean gates fell from `1.40` to `1.15`;
- final checkpoint regressed to `0.10` success and `0.90` crash;
- W&B pass/finish/gate-plane conversion remained flat.

The next test should keep the winning v5 observation/controller stack and the
loop052 checkpoint, but shift the reward numbers just enough to test whether
the policy can recover gate progress and pass conversion without losing the
current safety profile.

This is not the earlier loop051 aggressive gate-acquisition retune. That retune
used much larger gate/completion values from the loop050 branch and regressed.
The approved change here is smaller and starts from the stronger loop052 final
checkpoint.

## Approved Next Experiment

Name:

`v5_loop052_mild_gate_pressure_nominal_safety_20m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

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
  keep loop052 values, including `learning_rate=5e-5`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Reward-number changes versus loop052:

- `gate_stage_coef: 10.0 -> 12.0`
- `gate_axis_coef: 12.0 -> 16.0`
- `gate_bonus: 90.0 -> 120.0`
- `gate_back_bonus: 12.0 -> 20.0`
- `obstacle_coef: 8.0 -> 7.5`
- `obstacle_margin: 0.40 -> 0.35`
- `obstacle_clearance_coef: 6.0 -> 3.0`

All other numbers stay as in loop052.

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
  --proposal-name v5_loop052_mild_gate_pressure_nominal_safety_20m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 20000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_053_v5_remote_nominal_reward_maturation_from_loop052_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop053_mild_gate_pressure_from_loop052.md \
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
  --param gate_stage_coef=12.0 \
  --param gate_axis_coef=16.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=120.0 \
  --param gate_front_bonus=0.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=20.0 \
  --param finish_bonus=160.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=8.0 \
  --param crash_penalty=100.0 \
  --param obstacle_coef=7.5 \
  --param obstacle_margin=0.35 \
  --param obstacle_clearance_coef=3.0 \
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

Promote if hard eval on `config/level3_dr.toml` shows:

- success rate `> 0.20`; or
- mean gates `> 1.45`; or
- crash rate `< 0.80`; or
- success `0.20` with mean gates at least `1.40` and W&B pass/finish
  conversion improving.

Reject or change lane if:

- best success falls back to `<= 0.15`;
- mean gates stay below `1.20`;
- crash returns to `>= 0.85`;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` remain
  flat while evaluator progress regresses.

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then repeat the three-review decision gate before any further training.
