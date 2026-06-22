# Launch v31a Longer-Rollout Clean PPO Screen

Decision: `launch_named_structural_lane`

Status: approved for one bounded train/evaluate chunk.

## Scope

Final acceptance remains `config/level3.toml`.

Do not modify Level3 track geometry or randomization. `config/level3_dr.toml`
is training-only robustness context, not the final gate.

## Why This Supersedes the Seed43 v30-A Continuation

Loop093 showed corrected v30 episode semantics did not collapse and slightly
improved loop052 on final-target hard eval:

- loop052 final-target baseline: `16/100`, mean gates `1.43`;
- loop093: `17/100`, mean gates `1.55`, crash `83/100`.

That is not enough to promote v30-A, and the broader framework packet argues
that the main bottleneck is now training state distribution and credit
assignment, not another local reward or fixed-seed tweak.

## Hypothesis

`1024 envs x 32 steps` gives the critic and GAE only about `0.64s` of continuous
per-env experience per update. In Level3, gate approach/cross/recovery and
obstacle avoidance often span longer than that.

Keeping the batch size fixed while switching to:

```text
256 envs x 128 steps = 32768 samples/update
```

should improve temporal credit assignment without changing the deployed actor,
reward scale, track, observation layout, or PPO update sample count.

## Locked Variables

- initial checkpoint: loop052 final;
- actor observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- policy: 2x256 Tanh MLP;
- action path: legacy Normal policy plus environment clipping;
- reward structure and reward numbers: loop052 values;
- PPO hyperparameters: loop052 values;
- teacher KL: disabled;
- static seed replay: disabled;
- hard eval: `config/level3.toml` on validation_unseen seeds 101-200.

## Changed Variables

- `num_envs=256`;
- `num_steps=128`;
- `train_timesteps=5_000_000`;
- `checkpoint_interval=1_000_000`;
- validation milestone eval at 1M, 2M, 3M, 4M, 5M/final;
- training seed `43`.

## Promotion Screen

This lane is promising if it beats loop093 on either:

- success rate `> 0.17`; or
- mean gates `> 1.55`;

and especially if it reaches either:

- success rate `>= 0.20`; or
- mean gates `>= 1.60`.

If promising, prefer maturing this same hypothesis before jumping to reward
numbers. If not promising, the next structural support work should be
observation/return normalization or asymmetric critic, not speed tuning.

## Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v31a_longer_rollout_clean_ppo_5m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_093_structural_v30_episode_semantics_only_2m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_launch_v31a_longer_rollout_clean_ppo.md
```
