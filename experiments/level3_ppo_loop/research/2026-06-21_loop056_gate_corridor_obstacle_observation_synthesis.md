# Loop056 Gate-Corridor Obstacle Observation Synthesis

Date: 2026-06-21

## Scope

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry, gates, obstacles, and randomization are immutable.
- This packet supports one bounded observation-structure lane:
  `v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`.
- The lane starts from the current global best loop052 checkpoint and keeps
  loop052 reward, PPO, and controller settings fixed.

## Local Evidence

Current global best:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Hard-eval metrics on `config/level3_dr.toml`, seeds 1-20:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`

Recent loop052-derived failures:

- loop053 nominal maturation: success tied at `0.20`, mean gates fell to
  `1.15`, final checkpoint regressed.
- loop054 mild gate pressure: best success `0.15`, mean gates `1.20`.
- loop055 PPO update pressure: best success `0.15`, mean gates `1.05`.
- loop056 light soft-centerline plane shaping: best success `0.15`, mean gates
  `1.20`, final success `0.10`.

Loop056 taxonomy versus loop052:

- Gate count improved on only `2/20` hard-eval seeds, worsened on `3/20`, and
  stayed unchanged on `15/20`.
- Both policies still concentrate failures at gate0/gate1 and nearby
  obstacles.
- loop056 reshuffled success seeds instead of improving the cross-seed
  frontier.

Interpretation:

The last four loop052-derived branches falsify three common explanations:

- "needs more nominal steps" was tested by loop053.
- "needs stronger gate pressure" was tested by loop054 and earlier loop051.
- "needs more PPO movement" was tested by loop055.
- "needs light plane/centerline reward" was tested by loop056.

The remaining local failure pattern is early-gate survival and pass conversion
under obstacle interaction. That points to observation structure rather than
another reward-number scale.

## Source Evidence

Song et al., *Autonomous Drone Racing with Deep Reinforcement Learning*
(IROS 2021), motivate relative gate observations for drone racing policies:

- https://arxiv.org/abs/2103.08624
- https://rpg.ifi.uzh.ch/docs/IROS21_Yunlong.pdf

The relevant takeaway is not to copy their full setup, but to keep geometric
race context in the policy input. v5 already moved away from world-frame
obstacle clutter toward compact local gate/obstacle inputs. The observed
failure is more specific: the policy sees nearest obstacles in drone-heading
coordinates, but it does not explicitly see whether those obstacles sit inside
or near the current gate corridor.

The Swift drone-racing system describes the controller consuming a compact
low-dimensional representation produced by perception:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC10468397/

The relevant takeaway is that compact task geometry is a valid interface for a
racing controller. For this project, v8 keeps the compact v5 vector and adds
only gate-frame obstacle geometry, rather than restoring all-gates/world-frame
features.

Potential-based reward shaping remains relevant background for why another
unconstrained reward scale is risky:

- https://people.eecs.berkeley.edu/~pabbeel/cs287-fa09/readings/NgHaradaRussell-shaping-ICML1999.pdf

This packet does not launch another reward-shaping lane. It uses that evidence
only to support avoiding further ad hoc overlapping reward scales after
loop051/054/056 failed to convert.

## Proposed Observation Lane

Name:

`v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`

Observation layout:

`level3_gate_corridor_obstacle_relative_2obs_local_history_v8`

Feature design:

- Preserve the first 68 dimensions of v5 unchanged.
- Append 14 dimensions:
  - `target_progress`
  - drone position in the current target-gate frame: `x, y, z`
  - for each of the two nearest obstacles, in the same current target-gate
    frame: `x, y, z, lateral_dist, detected`

Why this is not v4:

- It does not restore all-gates observation.
- It does not add world-frame global obstacle lists.
- It keeps v5's compact local observation and appends only current-gate
  corridor geometry.

Why this is not v6/v7:

- v6 changed the second gate block from nearest-other gate to race-order next
  gate, but did not add obstacle corridor context.
- v7 appended target progress and gate-frame drone position, but did not tell
  the policy whether nearest obstacles conflict with the current gate corridor.
- v8 keeps v7's phase/current-gate-frame idea and adds obstacle positions in
  the same gate frame.

Why this is not loop051/054/055/056:

- It does not change reward numbers.
- It does not change PPO update pressure.
- It does not change reward structure.
- It keeps loop052 reward/PPO/controller settings fixed and changes only the
  observation structure.

## Training Plan

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Warm start:

- Zero-pad appended input weights from the loop052 v5 checkpoint.
- Keep hidden dim `256`.
- Start optimizer fresh.

Training:

- `30M` steps
- `5M` checkpoint interval
- W&B enabled under `ADR-PPO-Racing-Level3`
- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`

Keep loop052 settings:

- `learning_rate=5e-5`
- `update_epochs=5`
- `ent_coef=0.02`
- `target_kl=0.03`
- `reward_structure=legacy_staged`
- `gate_stage_coef=10`
- `gate_axis_coef=12`
- `gate_bonus=90`
- `gate_front_bonus=0`
- `gate_back_bonus=12`
- `finish_bonus=160`
- `wrong_side_penalty=8`
- `crash_penalty=100`
- `obstacle_coef=8`
- `obstacle_margin=0.4`
- `obstacle_clearance_coef=6`
- `time_penalty=0.03`
- action/smooth/tilt penalties unchanged from loop052.

## Promotion And Rollback

Promote or mature if the best checkpoint reaches at least one:

- success `>=0.25` on 20-seed hard eval;
- success `0.20` with mean gates `>1.40`, crash `<=0.80`, and mean successful
  time `<=7.0s`;
- success `>=0.15`, mean gates `>=1.40`, crash `<=0.85`, and W&B pass/finish
  plus gate-plane/corridor signals improve enough to justify a 60M maturation.

Rollback or hold if:

- best success stays `<=0.15`;
- crash stays `>=0.85`;
- mean gates remain below `1.40`;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` remain
  flat;
- taxonomy still shows the same early gate/obstacle crash concentration.

## Required Next Command Shape

The next command must:

- include `--max-iterations 1`;
- include `--wandb-enabled`;
- include `--wandb-entity aojili77-technical-university-of-munich`;
- include `--codex-autonomous-loop`;
- include `--structural-hypothesis v8_gate_corridor_obstacle_relative_obs_from_loop052`;
- attach the loop056 analysis packet;
- attach the main-agent v8 decision packet;
- dry-run before real training.
