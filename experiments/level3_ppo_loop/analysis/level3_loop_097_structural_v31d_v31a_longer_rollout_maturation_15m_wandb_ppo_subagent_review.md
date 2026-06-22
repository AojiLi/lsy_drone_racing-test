# W&B / PPO Diagnostics Review: loop097 / v31d

## Key Finding

PPO is stable, but the training signal is quiet and hard-eval conversion is
weak.

## Evidence

- `approx_kl=0.000361`.
- `clipfrac=0.000006`.
- entropy is flat at `4.184389`.
- explained variance is about `0.759573`.
- value loss trends down to `224.77774`.
- Teacher-retention metrics are inactive.
- Race metrics are mostly flat:
  `passed_gate_rate=0.005463`, `finished_rate=0.000153`,
  `crashed_rate=0.006805`.
- Hard-eval best is real but small: `20/100` success, `7.055s`, `80%` crash,
  and `1.66` mean gates.
- The success milestone curve was:
  `0.16, 0.12, 0.15, 0.18, 0.14, 0.16, 0.13, 0.20, 0.20, 0.19`.

## Recommended Next Action

The W&B/PPO view favors `change_reward_or_training_numbers`: keep PPO/training
structure fixed and apply a gate-acquisition reward adjustment if the main
agent decides not to mature the same hypothesis. Suggested fallback reward
numbers are:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- `time_penalty=0.02`

## Main-Agent Note

This is recorded as the fallback lane after a 30M-style continuation check, not
as the immediate next launch.

