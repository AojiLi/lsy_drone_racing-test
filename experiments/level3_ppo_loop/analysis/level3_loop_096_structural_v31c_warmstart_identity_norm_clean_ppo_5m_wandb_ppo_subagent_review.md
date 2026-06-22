# W&B / PPO Diagnostics Review: loop096 / v31c

## Key Finding

PPO did not numerically blow up, but updates did not convert into racing
behavior. v31c caused destructive training drift after parity had passed.

## Evidence

- Final `approx_kl`: `0.000247`.
- Final `clipfrac`: `0.0`.
- Final entropy: `4.590132`.
- Final explained variance: `-1.76228`.
- Final value loss: `12.996799`.
- Actor observation normalization looked numerically sane:
  `obs_var_mean=0.990045`, `obs_clipfrac=0.0`.
- Return normalization looked suspicious in raw scale:
  `return_mean=-393744.71875`, `return_var=1.6468e14`, while normalized
  `value_target_abs_mean` stayed near `1.98`.
- Gate-relevant W&B signals did not convert:
  `race/passed_gate_rate=0.0`, `race/finished_rate=0.0`,
  `reward_components/gate_bonus=0.0`, and gate-stage progress degraded.
- Crash rate improved from early v31c milestones, but this became
  non-progress/timeout behavior rather than successful racing.

## Recommended Next Action

Do not continue v31c. If normalization is revisited later, use a targeted
ablation lane such as disabled return normalization or frozen observation
statistics. For the next training chunk, prefer a named lane that avoids the
v31c normalization/training interaction.

