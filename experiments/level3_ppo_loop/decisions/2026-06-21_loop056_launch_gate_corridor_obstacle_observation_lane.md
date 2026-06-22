# Main-Agent Decision After Loop056

Date: 2026-06-21

## Decision

`launch_named_structural_lane`

## Latest Trial

Trial:

`level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m`

Best loop056 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m_step_005000000.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.96s`
- Crash: `0.85`
- Mean gates: `1.20`
- Target met: `false`

Global best remains loop052 final:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Global-best metrics:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`

## Required Reviews

Review packet:

`experiments/level3_ppo_loop/analysis/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m_subagent_reviews.md`

`evaluator_metrics`:

- Do not continue loop056.
- No recent branch beats loop052.
- If training proceeds, start from loop052 final.
- Promotion requires success `>=0.25`, or a `0.20` tie with better gates/crash.

`wandb_ppo_diagnostics`:

- Loop056 is a non-conversion run.
- W&B reward changed, but pass/finish/plane-cross rates stayed flat.
- KL and clip fraction were near zero, so the issue is not raw throughput.
- No training command is approved from W&B/PPO evidence alone.

`structure_research_synthesis`:

- Launch a new observation structural lane, not another reward scale.
- The untested axis is explicit current-gate corridor versus obstacle geometry.
- Preserve loop052 reward/PPO/controller settings and warm-start from loop052.

## Rationale

Loop056 met rollback conditions:

- best success stayed `<=0.15`;
- crash stayed `>=0.85`;
- W&B pass/finish/plane-cross signals stayed flat;
- final checkpoint regressed to `0.10` success.

The analyzer's aggressive gate-acquisition command overlaps with failed local
evidence from loop051, and loop054 already tested a milder gate-pressure move.
loop055 tested PPO update pressure. loop053 tested same-lane nominal
maturation. None beat loop052.

The next useful branch should therefore isolate one new structural variable.
The selected variable is observation structure: add compact gate-corridor
obstacle geometry while keeping reward, PPO, controller, train config, and hard
eval target fixed.

## Approved Next Lane

Name:

`v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`

Orchestrator structural hypothesis:

`v8_gate_corridor_obstacle_relative_obs_from_loop052`

Observation layout:

`level3_gate_corridor_obstacle_relative_2obs_local_history_v8`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-21_loop056_gate_corridor_obstacle_observation_synthesis.md`

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Training:

- `30M` steps
- `5M` checkpoint interval
- W&B enabled
- train config: `level3_dr.toml`
- hard eval config: `level3_dr.toml`

Structural change:

- Preserve v5's first 68 observation dimensions.
- Append 14 dimensions:
  - target progress;
  - drone position in the current target-gate frame;
  - nearest two obstacles in the current target-gate frame as
    `[x, y, z, lateral_dist, detected]`.

Everything else stays at the loop052 setting:

- `reward_structure=legacy_staged`
- `learning_rate=5e-5`
- `update_epochs=5`
- loop052 reward/action/smooth/tilt/safety numbers unchanged.

## Stop/Continue Criteria

Stop target met if hard eval reaches:

- success `>=0.60`; and
- mean successful time `<=7.0s`.

Promote or mature if the best checkpoint reaches at least one:

- success `>=0.25`; or
- success `0.20` with mean gates `>1.40`, crash `<=0.80`, and mean successful
  time `<=7.0s`; or
- success `>=0.15`, mean gates `>=1.40`, crash `<=0.85`, and W&B
  pass/finish/gate-plane signals improve enough to justify a 60M maturation.

Rollback or hold if:

- best success stays `<=0.15`; or
- crash stays `>=0.85`; or
- mean gates remain below `1.40`; or
- W&B pass/finish/gate-plane signals stay flat; or
- taxonomy still shows the same early gate/obstacle crash concentration.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v8_gate_corridor_obstacle_relative_obs_from_loop052 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop056_launch_gate_corridor_obstacle_observation_lane.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not use v4/all-gates observation.
- Do not run more than one train/eval iteration before post-run W&B/evaluator
  analysis and review.
