# Loop010 Step-Curve Maturation Packet

Date: 2026-06-18

## Decision

Run one bounded Level3 PPO maturation chunk from the current global-best
checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Train with the same existing `level3_dr_stage2_no_train_wrappers.toml` lane and
evaluate only on the hard target `level3_dr.toml`.

This packet does not approve a new observation layout, PPO hyperparameter
change, algorithm change, reward-channel addition, or new training structure.
It only approves maturing the already-tested loop010 lane because 30M is too
short to judge a promising PPO branch.

## Evidence

Local Level2 checkpoint step-curve review:

```text
experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md
```

Key Level2 result:

- 30M checkpoints were still 0%-2% success.
- 60M checkpoints reached 53%-75% success.
- 70M-95M was the first stable high-success region.
- The best checkpoint was sometimes an intermediate checkpoint, not final.

Local Level3 loop010 evidence:

- Hard eval config: `level3_dr.toml`
- Best checkpoint: `level3_loop_010_stage2_no_train_wrappers:15M`
- Success rate: `0.05`
- Mean successful time: `5.64s`
- Mean gates: `0.80`
- Crash rate: `0.95`

Interpretation:

- Loop010 is the only current branch with non-zero hard-eval Level3 success.
- The 15M/30M behavior is too early to reject under the Level2 step-curve
  calibration.
- A single maturation chunk can test whether the non-zero success signal grows
  when the same policy family is trained into the 60M-90M evidence region.

## Scope

Allowed for the next chunk:

- Continue from loop010 best checkpoint.
- Keep disabled reward channels at zero.
- Keep observation layout `obstacle_heading_xy_v1`.
- Keep PPO hyperparameters/network unchanged.
- Use milestone-aware checkpoint evaluation.
- Use W&B online logging.
- Hard-evaluate on `level3_dr.toml`.

Not allowed in this chunk:

- No reward-channel additions.
- No observation-layout changes.
- No algorithm/PPO hyperparameter changes.
- No new training-config/curriculum invention.
- No judging acceptance from training reward alone.

## Reward Numbers

Use the loop010 reward numbers exactly:

```text
gate_stage_coef=14
gate_axis_coef=28
gate_bonus=220
gate_front_bonus=10
gate_back_bonus=45
finish_bonus=190
wrong_side_penalty=8
crash_penalty=55
obstacle_coef=5.25
obstacle_margin=0.2
timeout_penalty=80
time_penalty=0.015
act_coef=0.015
d_act_th_coef=0.075
d_act_xy_coef=0.08
cmd_tilt_coef=0.9
rpy_coef=0.75
tilt_limit_deg=38
tilt_excess_coef=14
```

## Evaluation Plan

User approved expanding the maturation chunk to 100M so the loop can more
directly rule out the "not enough PPO steps" hypothesis and inspect W&B
convergence over a longer horizon.

Run one 100M extended maturation chunk:

- `--train-timesteps 100000000`
- `--checkpoint-interval 5000000`
- `--eval-checkpoint-strategy milestone`
- `--eval-milestones-m 30,60,90,100`
- `--max-eval-checkpoints 10`
- `--eval-seeds 20`

After the run, execute:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then decide:

- If success rate or mean gates improves, run a wider 100-seed confirmation on
  the best checkpoint or continue the same hypothesis only if W&B reward,
  gate/finish, and PPO diagnostics are still improving.
- If hard-eval success returns to zero and mean gates does not improve, reject
  the maturation and do not extend this lane blindly.
- If success increases but crash/cmd-tilt is still high, make one reward-only
  safety/smoothness adjustment before another long chunk.
- If W&B reward has flattened, gate/finish metrics do not convert, and hard eval
  does not improve, treat training-step insufficiency as unlikely for this
  branch and stop.

## Acceptance

Primary target remains:

- success rate `>= 0.60`
- mean successful time `<= 7.0s`

Interim improvement signals:

- success rate above the current global best `0.05`
- or mean gates clearly above `0.80`
- or crash rate below `0.95` without losing gate progress
