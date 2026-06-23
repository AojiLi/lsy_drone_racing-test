# Decision: Reject V48, Launch V49 Hidden512 Long-Horizon Baseline

Decision: launch_named_structural_lane

Trial resolved:
`level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_analysis.md`

Subagent review packet:
`experiments/level3_ppo_loop/analysis/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_subagent_reviews.md`

Next structural lane:
`v49_v5_hidden512_mlp_warmstart_from_loop110_3m`

## Decision

Reject v48 as-is. Do not continue from loop118 final, do not mature the
contact/conversion reward-structure hypothesis, and do not run another small
contact-reward tweak as the next move.

Launch the hidden512 long-horizon baseline:

`v49_v5_hidden512_mlp_warmstart_from_loop110_3m`

This is not a short 5M capacity check. The user correctly noted that expanding
the network from 2x256 to 2x512 is itself a structural change, so the new
network may need tens of millions of steps to adapt before its success rate is
meaningful. v49 therefore runs a `60M` baseline with milestone evaluation, then
the next decision stays inside the hidden512 family unless the run reveals a
real wiring/training failure or catastrophic loss of gate progress.

## Rationale

v48 regressed the hard evaluator:

- best checkpoint: `1M`;
- success rate: `16%`;
- mean gates: `1.50`;
- mean successful time: `6.516s`;
- crash rate: `84%`.

The current frontier remains loop107/v37 1M with `21%` success and `1.66` mean
gates, while loop110/v39 3M gives the best feed-forward v5 starting point at
`21%` success and `1.64` mean gates. Recent v45/v47/v48 lanes show that
retention and contact-reward pressure are not enough to break the plateau.

The Level2 checkpoint step curve argues against judging a structurally changed
policy too early:

- one Level2 branch had `0%` success at 30M, `43%` at 45M, and first exceeded
  `60%` at 70M;
- another had only `2%` success at 30M, but `75%` at 60M and `80%` at final.

Therefore v49 should isolate network capacity, but with a real long-horizon
read:

- start from loop110/v39 3M;
- keep v5 observation;
- keep v39 reward numbers;
- expand the 2-layer Tanh Actor/Critic from hidden_dim `256` to `512`;
- use `allow_hidden_dim_warmstart=True`;
- use step-curve maturation permission because loop110/v39 3M already has
  promising hard-eval evidence;
- run `60M` with milestone evals at `5M`, `10M`, `15M`, `20M`, `30M`, `45M`,
  and `60M`;
- keep hard eval on unchanged `config/level3.toml`.

## Guardrails

- Do not edit `config/level3.toml` track geometry, gates, obstacles, or
  randomization.
- Do not add inference-time teacher logic, planner logic, rule controllers,
  safety shields, or ensembles.
- Do not use loop118 checkpoints as the starting point.
- Do not inherit v48 `decoupled_frame_clearance` reward numbers.
- Do not run `--max-iterations > 1`.
- After v49 completes, run the analyzer and exactly three subagent reviews
  before any next training chunk.
- Do not reject the hidden512 family from early 5M-30M milestones.
- Do not reject the hidden512 family from one 60M v49 run unless it
  catastrophically loses basic gate progress across the long run or exposes a
  wiring/training bug.

## Promotion / Continuation / Rejection

Promote early if:

- success `>21%`; or
- success `>=21%` with mean gates above `1.66` and crash `<=79%`; or
- success-seed coverage expands without losing the old frontier.

Continue the same hidden512 hypothesis toward `90M` and possibly `120M` if:

- 60M has non-zero success with mean gates near the old frontier;
- mean gates improve across 30M/45M/60M;
- W&B gate/finish signals are still improving without PPO instability;
- the run finds a new useful solved-seed subset.

If v49 underperforms but still has meaningful gate progress, the next decision
should stay inside the hidden512 family and choose a targeted follow-up:

- hidden512 reward/PPO-number adjustment;
- hidden512 observation variant;
- hidden512 GRU or residual-GRU transfer;
- hidden512 curriculum or training-distribution reshaping.

Do not abandon the hidden512 base until at least three evaluated hidden512
family trials exist: the 60M baseline, one reward/PPO-number follow-up, and one
observation/memory/curriculum follow-up.

Hold for diagnosis, rather than reject the family, only if v49 has near-zero
success with mean gates below `0.50` throughout the long run, or if training /
evaluation wiring fails.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v49_v5_hidden512_mlp_warmstart_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v49_hidden512_baseline_loop_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop118_reject_v48_launch_v49_hidden512_baseline.md
```
