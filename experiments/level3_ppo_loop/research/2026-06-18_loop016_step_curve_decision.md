# Loop016 Step-Curve Decision Packet

## Trial

- Trial: `level3_loop_016_loop010_step_curve_maturation_100m`
- Train config: `level3_dr_stage2_no_train_wrappers.toml`
- Hard eval config: `level3_dr.toml`
- Initial checkpoint: `level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt`
- Scope: reward-only continuation, no observation/algorithm/PPO/training-structure changes.

## Hard Eval Result

| Checkpoint | Success | Mean gates | Crash | Mean success time |
| --- | ---: | ---: | ---: | ---: |
| 30M | 0.00 | 0.55 | 1.00 | n/a |
| 55M | 0.05 | 0.95 | 0.95 | 6.10 |
| 60M | 0.00 | 0.65 | 1.00 | n/a |
| 65M | 0.00 | 0.80 | 1.00 | n/a |
| 70M | 0.00 | 0.80 | 1.00 | n/a |
| 75M | 0.00 | 0.75 | 1.00 | n/a |
| 80M | 0.00 | 0.70 | 1.00 | n/a |
| 85M | 0.00 | 0.50 | 1.00 | n/a |
| 90M | 0.00 | 0.80 | 1.00 | n/a |
| 95M | 0.00 | 0.75 | 1.00 | n/a |
| final | 0.00 | 0.80 | 1.00 | n/a |

Best checkpoint:
`lsy_drone_racing/control/checkpoints/level3_loop_016_loop010_step_curve_maturation_100m/level3_loop_016_loop010_step_curve_maturation_100m_step_055000000.ckpt`

## W&B Summary

- `train/total_reward` increased, but hard evaluator progress did not convert.
- `race/passed_gate_rate` and `race/finished_rate` were flat.
- `race/gate_stage` was flat and `race/gate_axis_x` trended down.
- PPO diagnostics were stable (`approx_kl`, `clipfrac`, `explained_variance`), so this does not look like a PPO numerical-instability failure.
- Commanded tilt remained near saturation; `cmd_tilt_over_limit_frac` stayed around 0.94-0.95.

## Subagent Consensus

- Evaluator reviewer: do not continue this same branch to 150M/200M. The 55M result is an isolated peak, not a stable maturation curve.
- W&B reviewer: reward signals did not convert into Level3 evaluator success; PPO itself appears stable.
- Tuning reviewer: analyzer's suggested parameter move is within the reward-only whitelist, but increasing time pressure while success is only 5% and crash is 95% is not well justified.

## Decision

Do not launch a direct 150M/200M continuation from the loop016 branch.

Treat the original "insufficient training steps" hypothesis as mostly ruled out for this exact branch: 60M-100M did not improve success beyond the isolated 55M checkpoint.

Keep the 55M checkpoint as the current global best for resume/diagnosis, but do not treat it as close to target. It is still only 5% success versus the target 60%.

## Next Safe Actions

1. Optional confirmation: run a 100-seed hard eval on the 55M checkpoint to estimate whether 5% is real or sampling noise.
2. Before any next training chunk, write a reward-only hypothesis focused on reducing crash/commanded-tilt saturation while preserving gate acquisition.
3. Do not accept the analyzer's next command as-is without a main-agent decision, because it lowers gate/finish incentives and increases `time_penalty` despite very low success.

