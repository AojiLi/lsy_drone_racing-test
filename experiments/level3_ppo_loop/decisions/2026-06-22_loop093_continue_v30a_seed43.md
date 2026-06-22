# Loop093 Post-Run Decision: Continue v30-A Independent-Seed Screen

Decision: `continue_same_hypothesis`

Status: approved for one next v30-A training/evaluation chunk.

## Scope

The final acceptance target is `config/level3.toml`.

Do not modify Level3 track geometry or randomization. `config/level3_dr.toml`
remains a possible training-only robustness config, not the final acceptance
gate.

## Evidence

Loop093 tested `v30_episode_semantics_only_2m` from loop052 final with corrected
episode/reset/finish semantics, loop052 v5 observation layout, loop052 reward
numbers, and the legacy Normal policy.

Best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_093_structural_v30_episode_semantics_only_2m/level3_loop_093_structural_v30_episode_semantics_only_2m_final.ckpt`

Hard eval on `validation_unseen` seeds 101-200:

- success rate: `0.17`
- success count: `17 / 100`
- mean successful time: `7.04235294117647s`
- crash rate: `0.83`
- timeout rate: `0.00`
- mean gates: `1.55`
- termination reasons: `{"contact": 83, "finish": 17}`

Final-target loop052 baseline:

- success rate: `0.16`
- mean successful time: `6.77375s`
- crash rate: `0.84`
- mean gates: `1.43`

Loop093 is a tiny hard-eval improvement over loop052 on success, crash, and
mean gates, but it is not close to the target and is slightly slower on
successful episodes.

## Subagent Synthesis

Evaluator metrics:

- Loop093 is not promotable on metrics alone.
- Improvement over loop052 is small enough to be seed noise.
- The dominant failure pattern remains contact/bounds crashes, concentrated at
  target gate 0 and target gate 2.

W&B/PPO diagnostics:

- PPO did not numerically collapse.
- KL and clip fraction were near zero, so the policy may be updating too weakly.
- Before interpreting future reward changes, check policy/action-distribution
  drift across the 0.5M, 1M, 1.5M, and final checkpoints.

Structure/research synthesis:

- Do not accept the analyzer reward-number recommendation yet.
- v30-A was designed to isolate corrected episode semantics.
- Complete the intended independent-seed v30-A screen before moving to v30-B.

## Decision

Continue v30-A for one more independent seed. Keep the locked v30-A variables:

- initial checkpoint: loop052 final;
- actor observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- network: 2x256 MLP;
- reward structure and reward numbers: loop052 values;
- PPO hyperparameters: loop052 values;
- teacher KL: disabled;
- static seed replay: disabled;
- hard eval: `config/level3.toml` on `validation_unseen` seeds 101-200.

Change only the training seed from `42` to `43`.

This is not promotion. It is a replication screen. If the v30-A seed set remains
below the promotion gate, the next named structural lane should be v30-B
`v30_squashed_gaussian_episode_semantics_2m`, not reward tuning.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v30_episode_semantics_only_2m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_093_structural_v30_episode_semantics_only_2m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop093_continue_v30a_seed43.md \
  --research-packet experiments/level3_ppo_loop/decisions/2026-06-22_v30_semantics_audit_completed_level3_toml_parity.md \
  --param seed=43
```

## Required After Next Chunk

Run the post-run analyzer and the three required reviews before any further
training:

- evaluator metrics;
- W&B/PPO diagnostics;
- structure/research synthesis.

Also add a small policy/action drift diagnostic if KL and clip fraction remain
near zero.
