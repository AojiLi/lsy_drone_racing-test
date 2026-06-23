# Decision: Reject V48, Launch V49 Hidden512 Baseline Loop

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

Launch the new hidden512 baseline loop:

`v49_v5_hidden512_mlp_warmstart_from_loop110_3m`

This is not a one-off capacity curiosity. It starts a separate hidden512
capacity family. If the first screen does not degrade the frontier, later
reward, observation, GRU, curriculum, or training-distribution experiments
should be written as hidden512-family successor lanes.

Also, v49 alone must not be used as a simple pass/fail judgment on the larger
network. The hidden512 family should get multiple targeted follow-up loops
before being abandoned.

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

The user wants the larger network to become the new baseline before further
loop changes. v49 therefore isolates network capacity:

- start from loop110/v39 3M;
- keep v5 observation;
- keep v39 reward numbers;
- expand the 2-layer Tanh Actor/Critic from hidden_dim `256` to `512`;
- use `allow_hidden_dim_warmstart=True`;
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
- Do not reject the hidden512 family from v49 alone unless it catastrophically
  loses basic gate progress or exposes a wiring/training bug.

## Promotion / Rejection

Promote or mature v49 if:

- success `>21%`; or
- success `>=21%` with mean gates above `1.66` and crash `<=79%`; or
- success-seed coverage expands without losing the old frontier.

Use v49 as the temporary hidden512 baseline if it preserves the frontier
without clear degradation, even if it does not yet hit the final target.

If v49 underperforms but still has meaningful gate progress, the next decision
should stay inside the hidden512 family and choose a targeted follow-up:

- hidden512 reward/PPO-number adjustment;
- hidden512 observation variant;
- hidden512 GRU or residual-GRU transfer;
- hidden512 curriculum or training-distribution reshaping.

Do not abandon the hidden512 base until at least three evaluated hidden512
family trials exist: the baseline screen, one reward/PPO-number follow-up, and
one observation/memory/curriculum follow-up.

Hold for diagnosis, rather than reject the family, only if v49 has near-zero
success with mean gates below `0.50`, or if training/evaluation wiring fails.

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
