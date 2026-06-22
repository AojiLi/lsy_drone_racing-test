# Loop093 W&B/PPO Diagnostics Review

Role: W&B/PPO diagnostics

Final target: `config/level3.toml`

## Verdict

Loop093 did not numerically collapse, but the PPO update signal looks weak.

Observed W&B/PPO signals:

- `approx_kl` tail mean around `0.0003`, ending near zero;
- `clipfrac` at `0.0`;
- entropy roughly flat around `4.17`;
- explained variance stable around `0.786`;
- value loss drifting up;
- teacher-retention metrics inactive: teacher KL, teacher action MSE, and
  sampled batch size all zero.

Reward and race trends are mixed. Total reward improves, but sampled
`train/reward` trends down. Gate-stage and gate-axis signals improve slightly,
while gate bonus/crash-related components worsen. Hard-eval conversion remains
flat and crash-heavy.

## Risk

The policy may be updating too weakly. Before interpreting future reward
retunes as real learning, check policy parameter drift or action-distribution
drift across the 0.5M, 1M, 1.5M, and final checkpoints.

## Recommendation

Do not treat reward curves as success. If v30-A continues, preserve its
isolation and add a lightweight policy/action drift diagnostic if KL and
clipfrac stay near zero.
