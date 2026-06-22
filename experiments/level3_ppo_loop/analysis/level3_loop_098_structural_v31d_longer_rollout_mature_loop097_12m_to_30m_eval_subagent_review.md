# Evaluator Metrics Review: loop098

Verdict: reject continued v31d clean-PPO maturation.

Best loop098 checkpoint:

- `level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m:12M`
- Success: `19/100`
- Mean successful time: `7.496s`
- Crash rate: `81%`
- Timeout rate: `0%`
- Mean gates: `1.63`

Global best remains loop097:

- `level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m:12M`
- Success: `20/100`
- Mean successful time: `7.055s`
- Crash rate: `80%`
- Timeout rate: `0%`
- Mean gates: `1.66`

Delta from loop097 best to loop098 best:

- Success: `-1 pp`
- Mean gates: `-0.03`
- Mean successful time: `+0.441s` slower
- Crash rate: `+1 pp`
- Timeout rate: unchanged

Some loop098 checkpoints were faster under `7s`, especially 16M at `18%`
success / `1.67` gates / `6.986s`, but they lost success and crash rate versus
loop097 best. On evaluator evidence alone, v31d-to-30M plateaued or regressed
and remains far below the `60%` success target.

Recommended next action: `launch_named_structural_lane`, or hold until the main
agent decision packet names that lane. Do not continue v31d maturation.
