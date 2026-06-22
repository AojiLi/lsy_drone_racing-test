# Loop055 Remote-Nominal Soft-Centerline Synthesis

Date: 2026-06-21

## Scope

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry and randomization are immutable.
- This packet supports one bounded structural reward-lane screen from the
  current global best checkpoint.

## Local Evidence

Global best after loop055 remains:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Hard-eval metrics:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`

Loop053 matured the same nominal lane from loop052 and did not improve:

- Best success stayed `0.20`
- Mean gates fell to `1.15`
- Final regressed to `0.10` success

Loop054 increased gate pressure and nominal safety from loop052 and regressed:

- Best success `0.15`
- Final success `0.05`
- Final crash `0.95`

Loop055 increased PPO update pressure from loop052 and regressed:

- Best success `0.15`
- Best mean gates `1.05`
- Final success `0.05`
- Final crash `0.95`

W&B for loop055 showed PPO activity but no evaluator conversion:

- `losses/approx_kl` tail stayed low at about `0.0047` versus `target_kl=0.03`.
- `losses/clipfrac` tail stayed low at about `0.0092`.
- `train/reward` improved, but `race/passed_gate_rate`,
  `race/finished_rate`, and `race/gate_plane_cross_rate` stayed flat.
- `race/wrong_side_gate_rate` rose and obstacle distance fell.

## Source/History Evidence

The remote nominal reward addendum
`experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md`
identified a lower, smoother nominal reward scale that produced the current
local best after warm-start and Level3 DR adaptation.

Earlier structural attempts show what to avoid:

- `legacy_frame_clearance` with high event/backloaded rewards collapsed to
  zero success.
- `direct_aperture` made centered gate crossing too sparse/punitive and
  collapsed success.
- `soft_centerline_followthrough` with high loop020-style event rewards did
  not beat the frontier.
- v6/v7 observation probes did not beat the current loop052 checkpoint.

The remaining untested distinction is a low-scale soft centerline/followthrough
reward structure, using the loop052 nominal reward scale rather than the older
high event/backloaded scale.

## Proposed Lane

Name:

`v5_loop052_remote_nominal_soft_centerline_light_plane_20m`

Hypothesis:

Loop052 already has the best Level3 hard-eval conversion. More nominal steps,
more gate-pressure reward, and more PPO update pressure all failed. The next
bounded test should keep loop052's v5 observation, nominal PPO settings, and
safety scale, but change the reward structure so centered gate-plane crossing
and soft centerline followthrough are visible to the learner without the high
event-reward scale that failed in older lanes.

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Training:

- `20M` steps
- `5M` checkpoint interval
- v5 observation layout
- PPO reverted to loop052 nominal settings:
  `learning_rate=5e-5`, `update_epochs=5`

Reward structure:

- `reward_structure=soft_centerline_followthrough`
- Keep nominal remote scale for pass, finish, crash, obstacle, action, smooth,
  tilt, and time.
- Add light centered plane/followthrough signals:
  `gate_plane_bonus=16`, `missed_gate_penalty=6`,
  `gate_frame_pressure_coef=0.35`, `wrong_side_penalty=12`.

Promotion:

- Success rate greater than loop052's `0.20`; or
- success ties `0.20` with mean gates greater than `1.40`; or
- success `>=0.15` with mean gates `>=1.40`, crash `<=0.85`, and W&B
  gate-plane/finish signals improving.

Rollback:

- Best checkpoint stays `<=0.15` success with mean gates below `1.20`; or
- crash stays `>=0.85` and W&B gate/finish/plane-cross signals are flat; or
- final checkpoint regresses to `<=0.05` success.

