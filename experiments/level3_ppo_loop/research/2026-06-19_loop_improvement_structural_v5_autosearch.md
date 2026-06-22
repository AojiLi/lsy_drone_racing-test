# Loop Improvement: Structural v5 Autosearch

Date: 2026-06-19

## Reason

The loop was still operationally optimized for reward-only search even after the
user approved structural experiments. The best new external evidence from
`stateirving/lsy_drone_racing` points to the local-obstacle v5 observation lane,
not the rejected all-gates/v4 lane.

## Changes

- Added built-in structural hypothesis `v5_localobs_remote_reward`.
- Added `--structural-hypothesis v5_localobs_remote_reward` so the v5 lane can
  be launched without manually spelling out every reward parameter and packet.
- Added `--auto-structural-search`.
- Made `--codex-autonomous-loop` enable automatic structural search.
- Kept final hard eval immutable: `--eval-config` must be `level3_dr.toml`.
- Kept the first v5 run as a 30M screen with 5M checkpoints, matching the
  project's step-curve lesson that 30M is screening/debug evidence, not final
  rejection evidence.

## Built-In v5 Screen

The built-in hypothesis uses:

- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- start: from scratch
- train timesteps: `30_000_000`
- checkpoint interval: `5_000_000`
- reward scale: stateirving remote recipe
- source packet:
  `experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md`
- approval packet:
  `experiments/level3_ppo_loop/research/2026-06-19_user_approves_structural_search.md`

## Recommended Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --structural-hypothesis v5_localobs_remote_reward
```

