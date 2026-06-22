# Source-Backed Hypothesis: Legacy Centerline Safety Recovery

Date: 2026-06-20

## Context

The last two gate-potential trials did not move the Level3 frontier.

- loop028 showed short-horizon promise:
  - success rate: `0.15`
  - mean gates: `1.15`
  - crash rate: `0.85`
- loop029 matured the same gate-potential lane to 60M and collapsed:
  - best success rate: `0.0`
  - best mean gates: `0.7`
  - final mean gates: `0.05`
- loop030 increased true pass/finish reward inside gate-potential mode:
  - best success rate: `0.05`
  - best mean gates: `1.1`
  - later checkpoints returned to `0.0` success

The repeated failure mode is not training throughput. W&B and evaluator logs
show gate-stage proxies improving while real pass/finish conversion stays weak.

## Source Evidence

### Projection/Centerline Progress

Song et al., *Autonomous Drone Racing with Deep Reinforcement Learning*
(IROS 2021) use relative gate observations and a dense path-progress proxy
instead of relying only on sparse lap completion. Their reward projects progress
along line segments connecting adjacent gate centers and adds a safety term that
encourages passage through the gate center.

Source:
https://rpg.ifi.uzh.ch/docs/IROS21_Yunlong.pdf

Relevant takeaway for this repo:

- `legacy_staged` is closer to this style than `gate_potential`, because it
  retains continuous progress, axis progress, front-hit, pass, and back-hit
  events.
- `gate_potential` currently zeros `gate_front`, `gate_back`, and dense
  progress components, so analyzer recommendations involving those terms are
  ineffective unless the reward structure changes.

### Gate Progress Objective

Zhao et al., *Rethinking Reference Trajectories in Agile Drone Racing*
(ICRA 2026 project page / arXiv 2509.14726) emphasize directly maximizing
progress through gates rather than optimizing indirect trajectory-tracking
surrogates. They also describe temporally consistent gate-index switching only
after passing through the gate.

Source:
https://zhaofangguo.github.io/racing_mppi/

Relevant takeaway for this repo:

- The next RL lane should reward real gate progression and stable stage
  switching, not just a smooth approach proxy.
- This argues against continuing the current `gate_potential` formulation
  without changing the active event rewards.

### Obstacle/Gate Conflict And Curriculum

The CRL Drone Racing project and paper emphasize that obstacle-rich drone
racing has a real conflict between gate traversal and obstacle avoidance, and
that curriculum or staged training can help. The repository also states that
users should design curricula for their specific task.

Sources:

- https://arxiv.org/abs/2602.24030
- https://github.com/SJTU-ViSYS-team/CRL-Drone-Racing

Relevant takeaway for this repo:

- A later structural lane may need curriculum training.
- Before adding a curriculum, the lower-risk next test is to repair the active
  reward family that has actually produced the best local hard-eval result.

## Local Evidence

Best local Level3 hard-eval result:

- loop020 25M:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
  - reward structure: `legacy_staged`

Rejected evidence:

- loop026 continued loop020-style completion-backloaded rewards too long and
  collapsed to `0.0` success and `0.05` mean gates.
- loop027 used the analyzer's aggressive gate-acquisition numbers and regressed
  with high command tilt saturation:
  - success rate: `0.05`
  - mean gates: `0.8`
  - command tilt over-limit: `0.8259534779373124`
- loop029/loop030 show that gate-potential proxy progress does not convert to
  stable hard-eval passage.

## Hypothesis

Run one short, bounded `legacy_staged` recovery screen from loop020 25M.

Name:

`v5_legacy_centerline_safety_recovery_from_loop020_25m_30m`

Purpose:

- Return to the reward structure that produced the global best.
- Keep event rewards active: front hit, pass, back hit, finish.
- Emphasize centerline/gate-axis progress enough to improve gate acquisition.
- Increase safety/smoothness relative to loop027 so the policy does not simply
  saturate commands and crash.
- Use a 30M screen, not a 60M continuation, because loop026/029 showed that bad
  hypotheses can degrade after initially promising checkpoints.

## Proposed Parameters

Keep:

- observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- start checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- PPO/training settings:
  - `learning_rate=0.0003`
  - `gamma=0.99`
  - `gae_lambda=0.95`
  - `update_epochs=5`
  - `num_minibatches=8`
  - `ent_coef=0.02`
  - `target_kl=0.03`
  - `hidden_dim=256`
  - `n_obs=2`
- action authority:
  - `action_rp_limit_deg=90.0`
  - `action_lowpass_alpha=1.0`

Reward/training numbers:

- `reward_structure=legacy_staged`
- `progress_coef=0.0`
- `gate_stage_coef=11.0`
- `gate_axis_coef=28.0`
- `near_gate_coef=0.0`
- `gate_bonus=190.0`
- `gate_front_bonus=12.0`
- `gate_plane_bonus=0.0`
- `gate_back_bonus=45.0`
- `finish_bonus=240.0`
- `missed_gate_penalty=0.0`
- `wrong_side_penalty=12.0`
- `crash_penalty=70.0`
- `obstacle_coef=5.5`
- `obstacle_margin=0.3`
- `obstacle_clearance_coef=0.0`
- `timeout_penalty=80.0`
- `time_penalty=0.01`
- `act_coef=0.018`
- `d_act_th_coef=0.08`
- `d_act_xy_coef=0.08`
- `cmd_tilt_coef=1.05`
- `rpy_coef=0.9`
- `tilt_limit_deg=40.0`
- `tilt_excess_coef=16.0`

## Why This Is Not loop027 Again

loop027 used:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- weak smoothness/safety relative to the resulting saturation

This lane uses a different balance:

- higher centerline/axis pressure: `28.0`
- moderate front/back events: `12.0` / `45.0`
- less extreme finish backloading than loop020: `240.0` instead of `300.0`
- stronger crash/tilt/smooth penalties than loop027

The intended behavior is gate-centered acquisition without the loop027 command
saturation failure.

## Promotion And Rollback

Promote or mature only if a checkpoint beats at least one frontier:

- success rate above loop020/loop028: `>0.15`, or
- mean gates above loop020: `>1.45`, or
- same success with materially lower crash/tilt.

Reject if:

- best success is `<=0.05`,
- mean gates stay below `1.15`,
- command tilt over-limit exceeds `0.65` without evaluator improvement,
- or W&B pass/finish conversion remains flat.

Hard boundary:

- Do not modify `config/level3_dr.toml` track geometry, gate layout, obstacle
  layout, or randomization.
- Final acceptance remains hard eval on `config/level3_dr.toml`.
