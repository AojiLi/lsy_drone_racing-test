# Decision: Reject v31c and Continue v31a Maturation

Decision: `launch_named_structural_lane`

Approved next lane: `v31d_v31a_longer_rollout_maturation_15m`

## Scope

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry or randomization.
- Deployment remains end-to-end PPO actor to roll/pitch/yaw/thrust.
- `config/level3_dr.toml` remains training-only robustness evidence and is not
  the acceptance gate.

## Evidence

v31c passed zero-update parity from an identity-normalized loop094/v31a 4M
checkpoint, proving the wrapped checkpoint itself preserved behavior. After
training, however, every v31c milestone had `0/100` success on
`validation_unseen` seeds 101-200. The final checkpoint had:

- success rate: `0.00`;
- mean successful time: `None`;
- crash rate: `0.84`;
- timeout rate: `0.16`;
- mean gates: `0.0`;
- all failures still targeting gate 0.

The current global best remains loop094/v31a 4M:

`lsy_drone_racing/control/checkpoints/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt`

with `19/100` success, mean successful time `6.8758s`, crash `81%`, and mean
gates `1.55`.

## Reviewer Synthesis

- Evaluator reviewer: reject v31c; trained checkpoints lost loop094's gate
  progress and success frontier.
- W&B/PPO reviewer: no numerical PPO blow-up, but updates did not convert;
  return normalization scale is suspicious and v31c training drift was
  destructive.
- Structure/research reviewer: reject v31c; asymmetric privileged critic is a
  valid next roadmap stage only after trainer/evaluator support and parity
  checks exist.

## Next Lane

Run `v31d_v31a_longer_rollout_maturation_15m`.

This lane:

- starts from loop094/v31a 4M, the current best checkpoint;
- keeps v5 observations;
- keeps loop052 reward/PPO numbers;
- keeps corrected v30 episode/reset/finish semantics;
- keeps observation and return normalization disabled;
- keeps `256 envs x 128 steps`;
- hard-evaluates 1/2/3/4/5/8/10/12/15M milestones on `config/level3.toml`.

## Rationale

The only recent branch with real Level3 success is the clean longer-rollout
v31a branch. The normalization branches v31b and v31c both failed, and v31c
showed that normalization-enabled training can erase the current best behavior
even when zero-update parity passes. Before implementing a larger framework
change such as asymmetric privileged critic, take one bounded maturation chunk
from the best v31a checkpoint and let milestone hard eval decide whether longer
training improves the success frontier.

## Launch Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v31d_v31a_longer_rollout_maturation_15m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_096_structural_v31c_warmstart_identity_norm_clean_ppo_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop096_reject_v31c_continue_v31a_maturation.md
```

## Rollback / Stop Conditions

- If all v31d milestones stay at or below loop094/v31a 4M without new success
  seeds or mean-gate expansion, reject v31d and move to a trainer-support
  implementation lane such as asymmetric privileged critic.
- If any checkpoint approaches or exceeds the current best success frontier,
  analyze W&B plus hard-eval traces before deciding whether to mature further.

