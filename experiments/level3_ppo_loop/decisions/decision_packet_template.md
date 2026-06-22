# Level3 Post-Run Decision Packet Template

Use this template after `scripts/analyze_level3_ppo_trial.py` creates
`pending_post_run_decision`.

## Trial

- Trial id:
- Analysis report:
- Analysis JSON:
- W&B run:
- Best checkpoint:
- Hard-eval success rate:
- Mean successful time:
- Crash rate:
- Mean gates:
- Target met:

## Subagent Findings

- `evaluator_metrics`:
- `wandb_ppo_diagnostics`:
- `structure_research_synthesis`:

## Main-Agent Decision

Choose exactly one:

- `stop_target_met`
- `hold_for_more_analysis`
- `continue_same_hypothesis`
- `change_reward_or_training_numbers`
- `launch_named_structural_lane`

Selected decision:

## Rationale

- Local evaluator evidence:
- W&B evidence:
- PPO/training evidence:
- Structural or code evidence:
- External research evidence, if used:

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --analysis-packet experiments/level3_ppo_loop/analysis/<trial>_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/<this-file>.md
```

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- If launching a structural lane, name it explicitly and record observation,
  controller, reward structure, PPO/training, and checkpoint-horizon changes.
- If continuing the same hypothesis, state why the latest checkpoint is
  promising enough to mature.
- If changing only numbers, list every changed parameter.
