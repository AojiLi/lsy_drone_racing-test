# Level3 Trial level3_loop_005_auto_precision_low_pressure: Wandb Analysis Brief

## Task

Evaluate W&B curves. Focus on train reward, reward components, race metrics, KL, clip fraction, entropy, explained variance, and regressions.

## Evidence

- Report: `experiments/level3_ppo_loop/analysis/level3_loop_005_auto_precision_low_pressure_analysis.md`
- JSON: `experiments/level3_ppo_loop/analysis/level3_loop_005_auto_precision_low_pressure_analysis.json`

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Keep disabled reward channels at zero unless the user explicitly changes scope.

## Output

- Key finding:
- Evidence:
- Reward-only recommendation:
- Risk/rollback condition:
