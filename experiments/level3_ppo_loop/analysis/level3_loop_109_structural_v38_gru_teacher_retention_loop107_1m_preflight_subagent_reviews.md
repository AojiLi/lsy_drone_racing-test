# Loop109 Subagent Reviews

Trial:
`level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight`

Analysis:
`experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_analysis.md`

## Evaluator Metrics

Finding: reject v38 as an evaluator improvement.

Best v38 checkpoint:

- checkpoint: step `001000000`
- success: `18%`
- mean gates: `1.64`
- crash: `82%`
- mean successful time: `6.844s`

Comparison:

- vs loop107 1M: `-3pp` success, `-0.02` mean gates, `+3pp` crash,
  `0.734s` faster among successful episodes.
- vs loop101 final: `-2pp` success, `-0.05` mean gates, `+2pp` crash,
  `0.029s` faster among successful episodes.

Recommendation: do not promote or mature v38 as-is. The speed gain is on a
smaller successful subset and does not compensate for worse success, gate
depth, and crash rate.

## W&B / PPO Diagnostics

Finding: retention was active and numerically healthy, but did not convert into
hard-eval progress.

Evidence:

- `retention/sampled_batch_size`: `512`
- `losses/teacher_kl`: `0.0190 -> 0.0096`
- `losses/teacher_action_mse`: `0.0043 -> 0.00175`
- `retention/teacher_agreement`: `0.952 -> 0.9897`
- `losses/approx_kl`: `0.000681`
- `losses/clipfrac`: `0.000006`
- entropy stayed around `4.34`
- explained variance stayed around `0.75`
- value loss improved from about `306` to `234`

Diagnosis: this is not a PPO instability or retention-not-running failure.
Policy updates were conservative and the retained teacher behavior did not
increase gate acquisition. Training race metrics stayed weak: passed-gate and
gate-stage rates were flat or down, finish rate remained tiny, and crash rate
nudged up.

Recommendation: do not continue v38 as-is. The next step should either change
gate-acquisition reward/training numbers or launch a named variant that loosens
or redesigns retention.

## Structure / Research Synthesis

Finding: reject v38 as-is and do not start from loop109 checkpoints.

Evidence:

- v38 retention was active: sampled batch `512`, teacher agreement near
  `0.990`, KL near `0.0096`.
- best hard eval still fell below both frontiers:
  - loop107 1M: `21%` success / `1.66` mean gates / `79%` crash
  - loop101 final: `20%` success / `1.69` mean gates / `80%` crash
  - loop109 best: `18%` success / `1.64` mean gates / `82%` crash

Recommendation: return to the loop101/loop107 frontier and run a named
gate-acquisition reward/training-number screen, using unchanged
`config/level3.toml` and actor-only deployment. Prefer the stable feed-forward
loop101 final checkpoint for the next screen rather than continuing GRU
retention.

Suggested lane name:

```text
v39_feedforward_gate_acquisition_reward_rebalance_loop101_final
```
