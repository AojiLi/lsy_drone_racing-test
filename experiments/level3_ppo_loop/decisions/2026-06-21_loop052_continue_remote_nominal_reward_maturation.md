# Main-Agent Decision After loop052

Date: 2026-06-21

## Trial

- Trial:
  `level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m`

Best loop052 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Hard-eval metrics:

- Success rate: `0.20`
- Mean successful time: `6.975s`
- Crash rate: `0.80`
- Timeout rate: `0.00`
- Mean gates: `1.40`
- Mean action delta: `0.28385888628544`
- Mean max commanded tilt: `54.981531290036344deg`
- Commanded tilt over-limit fraction: `0.30566323226202763`

This is the current global best by success and crash rate. It does not meet the
final target of success `>= 0.60`, but it improves the prior frontier:

- loop020: success `0.15`, crash `0.85`, mean gates `1.45`
- remote safer anchor: success `0.15`, crash `0.85`, mean gates `1.45`
- loop051: success `0.10`, crash `0.90`, mean gates `1.15`
- loop052: success `0.20`, crash `0.80`, mean gates `1.40`

## Subagent Findings

- `evaluator_metrics` recommended `continue_same_hypothesis`.
  It found loop052 is not target-met but is the strongest hard-eval signal so
  far and satisfies the step-curve maturation rule.
- `wandb_ppo_diagnostics` recommended `continue_same_hypothesis`.
  It found no PPO instability: KL is low, clipfrac is near zero, explained
  variance is usable, value loss is stable, and SPS is healthy. W&B race
  metrics are not yet strongly converting, so the next run must verify
  conversion.
- `structure_research_synthesis` recommended `continue_same_hypothesis`.
  It found loop052 validates the remote nominal reward DR lane as promising and
  advised deferring the analyzer's immediate gate-acquisition retune.

## Main-Agent Decision

Selected decision:

`continue_same_hypothesis`

Continue the remote nominal reward DR lane from the loop052 final checkpoint
toward a 60M-style maturation run. Do not change reward numbers, observation
layout, controller, PPO structure, or Level3 track.

## Rationale

The analyzer suggested a gate-acquisition retune because mean gates remain low.
That recommendation is recorded but rejected for the immediate next move.

Reason: loop052 is the first lane to beat the `0.15` hard-eval success frontier.
The Level2 step-curve policy says a promising 30M branch should be matured to
60M-90M before rejection. Changing reward numbers immediately would confound
whether the remote nominal reward lane is actually improving with more steps.

The useful question for loop053 is therefore narrow:

Can the same remote nominal reward lane, continued from loop052 final, preserve
or improve `0.20` success and push mean gates beyond `1.45` without losing the
smoother control profile?

## Approved Next Experiment

Name:

`v5_remote_nominal_reward_maturation_from_loop052_30m`

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
  `learning_rate=5e-5`, `hidden_dim=256`, `n_obs=2`
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- Use `--allow-step-curve-maturation`
- W&B project: `ADR-PPO-Racing-Level3`

Keep the loop052 reward/training numbers:

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
  --allow-step-curve-maturation \
  --proposal-name v5_remote_nominal_reward_maturation_from_loop052_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop052_continue_remote_nominal_reward_maturation.md \
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

Promote if hard eval on `config/level3_dr.toml` shows:

- success rate `> 0.20`; or
- mean gates `> 1.45`; or
- crash rate `< 0.80`; or
- success `0.20` with mean gates at least `1.45` and no loss of smoother
  action/tilt profile.

Continue toward 90M only if the 60M-style read is at least neutral-positive.

Reject or change lane if:

- best success falls back to `<= 0.15`;
- mean gates stay below `1.40`;
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
