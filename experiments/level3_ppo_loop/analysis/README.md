# Level3 PPO Post-Run Analysis

This folder stores analysis packets produced after each completed Level3 loop
trial.

Run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich
```

The analyzer writes:

- `<trial_id>_analysis.md`: reader-facing report for the main agent
- `<trial_id>_analysis.json`: bounded machine-readable snapshot
- `<trial_id>_eval_subagent_brief.md`: evaluator-metric review brief
- `<trial_id>_wandb_subagent_brief.md`: W&B-curve review brief
- `<trial_id>_tuning_subagent_brief.md`: reward-only tuning synthesis brief

## Analysis Contract

- Evaluator metrics decide whether the hard gate is met.
- W&B curves explain why a run moved: reward components, race metrics, PPO
  diagnostics, throughput, and regressions.
- PPO diagnostics such as KL, clip fraction, entropy, and explained variance
  are diagnostic only. They do not authorize tuning PPO hyperparameters in this
  loop.
- The final next move must stay inside the active reward whitelist documented in
  `experiments/level3_ppo_loop/README.md`.
- Disabled reward channels stay at zero unless the user explicitly changes the
  loop scope.
