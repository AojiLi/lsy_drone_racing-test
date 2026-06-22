# Level3 PPO Research Packets

This folder stores external evidence used to decide the next reward-only tuning
move.

Use this flow:

1. Send `subagent_brief.md` to parallel research agents.
2. Collect their source-backed findings.
3. Write a main-agent synthesis from `synthesis_template.md`.
4. Attach that synthesis to the next loop run:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --research-packet experiments/level3_ppo_loop/research/<synthesis>.md
```

The loop records attached packets in `state.json` so each trial keeps its tuning
provenance.

Research packets may guide only active reward coefficient scaling. They must
not propose PPO hyperparameter changes, observation changes, algorithm changes,
curriculum changes, training-structure changes, or new reward channels unless
the structural-escalation gate in `experiments/level3_ppo_loop/README.md` is
met.

If reward-only tuning appears exhausted, use `escalation_template.md` instead
of a normal reward-scaling synthesis. The escalation packet must be detailed
enough for the main agent to decide whether Stage 2 structural work is justified.
