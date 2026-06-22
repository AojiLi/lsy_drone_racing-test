# Level3 PPO Decision: Safety + Axis Recovery After Loop 005

## Objective

Train `config/level3_dr.toml` toward the hard evaluator gate:

- Success rate `>= 0.60`
- Mean successful race time `<= 7.0s`

This packet approves one Stage 1 reward-only hypothesis. It does not approve
algorithm, observation, PPO hyperparameter, training-structure, curriculum, or
new reward-channel changes.

## Local Evidence

Latest evaluated trial: `level3_loop_005_auto_precision_low_pressure`.

- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_005_auto_precision_low_pressure/level3_loop_005_auto_precision_low_pressure_final.ckpt`
- Success rate: `0.0`
- Crash rate: `1.0`
- Mean gates: `0.70`
- Mean successful time: `null`
- `cmd_tilt_over_limit_frac`: `0.8923`
- `mean_smooth_penalty_per_step`: `0.0662`

Current global best remains:

- `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Success rate: `0.0`
- Crash rate: `1.0`
- Mean gates: `0.85`
- `cmd_tilt_over_limit_frac`: `0.7158`

W&B/analyzer evidence for 005:

- `race/finished_rate` tail mean: `0.0`
- `race/passed_gate_rate` flat near `0.0068`
- `race/gate_axis_x` worsened
- PPO diagnostics did not show policy-update explosion:
  `losses/approx_kl` and `losses/clipfrac` stayed flat/low

Diagnosis: 005 increased completion/gate-event incentives while lowering
safety pressure. The policy did not convert those incentives into real gate
passes or finishes; it became more aggressive and less controlled.

## Subagent Consensus

Evaluator review:

- Do not continue from 005.
- Roll back to the global best baseline checkpoint.
- Structural escalation is not eligible yet.

W&B review:

- Training reward improved, but evaluator progress did not convert.
- `cmd_tilt` and smoothness diagnostics worsened.
- Next move should restore safety pressure while preserving gate guidance.

Reward/research reviews:

- Do not run `auto_completion_backloaded`.
- Do not run pure `stability_first`.
- Run a custom `safety_axis_recovery` reward-only hypothesis from the best
  baseline checkpoint.

## External Evidence

- OpenAI Spinning Up PPO:
  PPO update diagnostics should be monitored, but current 005 KL/clip evidence
  does not justify PPO hyperparameter changes.
  https://spinningup.openai.com/en/latest/algorithms/ppo.html
- Stable-Baselines3 RL tips:
  Use informative shaped rewards and separate evaluation; evaluator metrics
  remain the acceptance gate, not training reward alone.
  https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html
- Champion-level Drone Racing, Nature 2023:
  Competitive drone-racing reward design balances progress/perception,
  smooth command, and crash penalties; lap crashes are invalid.
  https://www.nature.com/articles/s41586-023-06419-4
- Song et al., Autonomous Drone Racing with Deep RL:
  Sparse finish/lap rewards create credit-assignment difficulty; shaped gate
  progress and safety terms are needed, with a risk/progress tradeoff.
  https://rpg.ifi.uzh.ch/docs/IROS21_Yunlong.pdf
- MonoRace technical report:
  Task completion, flight smoothness, and crash penalty are balanced; motor
  penalties help suppress bang-bang control in early policies.
  https://arxiv.org/html/2601.15222v1
- Obstacle-aware autonomous drone racing:
  Wrong-side approaching, waypoint passing, timeout, and collision terms should
  be balanced rather than replaced by terminal completion bonuses.
  https://arxiv.org/html/2411.04246v1
- Drone-Racing-RL open-source example:
  Gate crossing is the main event signal; speed/time optimization comes after
  basic gate traversal works.
  https://github.com/vismaychuriwala/Drone-Racing-RL
- PyFlyt QuadX-Waypoints:
  Target reward and crash/out-of-bounds penalties are same-order signals, with
  progress and angular-rate penalties shaping behavior.
  https://github.com/jjshoots/PyFlyt

## Approved Hypothesis

Name: `custom_safety_axis_recovery`

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`

Intent:

- Restore safety and smoothness pressure above 004/005.
- Keep gate-axis and gate-stage guidance strong enough to avoid a purely
  conservative policy.
- Keep completion and back-side bonuses moderate because 005 showed zero
  finish conversion.
- Remove speed pressure for this screening chunk.

Approved active reward parameters:

```text
gate_stage_coef=13.0
gate_axis_coef=30.0
gate_bonus=205.0
gate_front_bonus=10.0
gate_back_bonus=40.0
finish_bonus=180.0
wrong_side_penalty=10.0
crash_penalty=80.0
obstacle_coef=7.0
obstacle_margin=0.23
timeout_penalty=80.0
time_penalty=0.0
act_coef=0.023
d_act_th_coef=0.11
d_act_xy_coef=0.11
cmd_tilt_coef=1.15
rpy_coef=1.05
tilt_limit_deg=36.0
tilt_excess_coef=20.0
```

Disabled reward channels must stay at `0`:

```text
progress_coef=0
near_gate_coef=0
gate_plane_bonus=0
missed_gate_penalty=0
obstacle_clearance_coef=0
```

## Decision Rules After Next 30M Chunk

Continue or refine this branch only if at least one of the following appears:

- `mean_gates > 0.85`
- `crash_rate < 1.0`
- W&B `race/passed_gate_rate` rises with lower tilt pressure
- W&B `race/finished_rate` becomes consistently nonzero

Rollback/hold this branch if any of the following remains true:

- `success_rate == 0` and `mean_gates <= 0.85`
- `cmd_tilt_over_limit_frac > 0.75`
- W&B `race/finished_rate` tail mean is `0` and `race/passed_gate_rate` is flat

## Structural Escalation Status

Do not structurally escalate yet.

Known evidence so far:

- Evaluated reward-only trials: `4`
- Distinct active-reward hypotheses: at least `3`
- Evaluated reward-only timesteps: about `150M`
- Target success: not met

The exhaustion gate still requires at least `6` evaluated reward-only trials,
at least `4` distinct reward hypotheses, at least `4` consecutive
no-improvement trials, W&B non-conversion evidence, and subagent agreement from
the full escalation audit set. This packet authorizes only the next reward-only
screening chunk.
