# Main-Agent Decision After Loop057

Date: 2026-06-21

## Decision

`continue_same_hypothesis`

## Latest Trial

Trial:

`level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`

Best loop057 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_step_025000000.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.153333333333333s`
- Crash: `0.85`
- Mean gates: `1.40`
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

`experiments/level3_ppo_loop/analysis/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_subagent_reviews.md`

`evaluator_metrics`:

- Continue v8 once from the 25M checkpoint.
- Rationale: non-zero hard-eval success and loop052-level mean gates at 25M.
- Do not change reward numbers.

`wandb_ppo_diagnostics`:

- Hold from W&B/PPO evidence alone.
- W&B pass/finish/gate-cross signals stayed flat.
- PPO updates were conservative and final regressed.

`structure_research_synthesis`:

- Hold from structural evidence alone.
- Do not repeat gate pressure, PPO pressure, soft-centerline, or v8 blindly.

## Additional Diagnostics

Diagnostic packet:

`experiments/level3_ppo_loop/diagnostics/2026-06-21_loop057_v8_vs_loop052_episode_taxonomy_synthesis.md`

Hard-eval seed comparison:

- v8 improved gate count on `5/20` seeds.
- v8 worsened gate count on `3/20` seeds.
- v8 added success on seed `1`.
- v8 lost loop052 success seeds `13` and `16`.

Crash taxonomy, diagnostic replay only:

- loop052 final: `3/20` successes, `17/20` crashes.
- loop057 v8 25M: `4/20` successes, `16/20` crashes.
- v8 reduced gate0 crash concentration but shifted more failures to gate1.

## Main-Agent Rationale

This is a borderline decision.

The negative evidence is real:

- loop057 did not beat loop052 on hard eval;
- success and crash hit the original rollback threshold;
- W&B pass/finish/gate-plane rates stayed flat;
- final checkpoint regressed.

The positive evidence is also real:

- 25M has non-zero hard-eval success;
- 25M ties loop052 on mean gates;
- successful episodes are faster than loop052;
- hard-eval gate count improves on more seeds than it worsens;
- taxonomy replay shows a weak positive shift in early-gate crash distribution.

The user's standing training-horizon rule and the Level2 step-curve packet say
not to reject a branch at 30M when it has non-zero hard-eval success or
meaningful gate progress. Therefore v8 gets exactly one guarded maturation.
This is not an acceptance of v8 as better; it is a step-count audit to avoid
rejecting a borderline structural signal too early.

## Approved Next Action

Continue the same v8 hypothesis from the 25M checkpoint to a 60M maturation
chunk.

Use:

- same observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`;
- same reward structure and numbers as loop052/loop057;
- same PPO/training numbers as loop057;
- same controller settings;
- train config `level3_dr.toml`;
- hard eval config `level3_dr.toml`.

Do not use loop057 final checkpoint.

## Promotion And Rollback

Promote if the best milestone checkpoint reaches at least one:

- success `>0.20`; or
- success `0.20` with crash `<=0.80`, mean gates `>1.40`, and mean successful
  time `<=7.0s`; or
- target met: success `>=0.60` and mean successful time `<=7.0s`.

Rollback or hold if:

- best success stays `<=0.15`;
- crash stays `>=0.85`;
- mean gates do not exceed `1.40`;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` stay
  flat;
- final checkpoint again regresses without a better intermediate checkpoint.

If rollback triggers, return to loop052 as the global-best anchor and do not
launch another v8 continuation without a new source-backed packet.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --train-timesteps 60000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v8_gate_corridor_obstacle_relative_obs_from_loop052 \
  --proposal-name v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_step_025000000.ckpt \
  --allow-step-curve-maturation \
  --allow-repeat-params \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_analysis.md \
  --analysis-packet experiments/level3_ppo_loop/diagnostics/2026-06-21_loop057_v8_vs_loop052_episode_taxonomy_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop057_continue_v8_gate_corridor_maturation.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not use v4/all-gates observation.
- Do not run more than one train/eval iteration before analyzer and review.
- Do not execute the analyzer's aggressive gate-acquisition reward command.
