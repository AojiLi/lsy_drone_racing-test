# Level3 PPO Tuning Synthesis: <date-or-trial>

## Local Evidence

- Last trial:
- Best checkpoint:
- Success rate:
- Mean successful time:
- Crash rate:
- Timeout rate:
- Mean gates:
- W&B run:

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout,
  network/training structure, curriculum, or add new reward channels.
- Allowed parameter overrides must come from the active reward whitelist in
  `experiments/level3_ppo_loop/README.md`.

## External Evidence Considered

| Source | Relevant finding | Confidence | Link |
| --- | --- | --- | --- |
|  |  |  |  |

## Diagnosis

- Primary bottleneck:
- Secondary bottleneck:
- What not to optimize yet:

## Next Experiment

- Hypothesis:
- Start mode: from scratch / continue best checkpoint
- Train timesteps:
- Checkpoint interval:
- Eval seeds:
- Parameter overrides:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --research-packet experiments/level3_ppo_loop/research/<this-file>.md
```

## Expected Signal

- W&B metrics that should improve:
- Evaluator metrics that should improve:
- Failure signal:

## Decision Rule After Run

- If improved:
- If unchanged:
- If worse:
