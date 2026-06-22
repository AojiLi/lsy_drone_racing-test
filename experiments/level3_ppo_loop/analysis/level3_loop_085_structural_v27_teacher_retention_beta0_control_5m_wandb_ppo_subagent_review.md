# Loop085 W&B/PPO Diagnostics Review

Role: wandb_ppo_diagnostics

Trial:
`level3_loop_085_structural_v27_teacher_retention_beta0_control_5m`

## Verdict

Reject beta=0 continuation. PPO diagnostics do not show a simple optimizer
collapse, but W&B training signals do not convert into validation success.

## PPO Diagnostics

The run appears numerically stable:

- approx_kl: about 0.004 to 0.005, below target_kl 0.03
- clipfrac: about 0.012 to 0.017
- entropy: about 6.68
- explained_variance: about 0.78 to 0.80
- no obvious entropy collapse, KL explosion, or value-loss runaway

## Conversion Failure

W&B train reward and some gate-stage proxies improved, but hard-eval did not:

- `race/passed_gate_rate` stayed essentially flat
- `race/finished_rate` stayed essentially flat
- validation best was only 10% success
- validation final regressed to 8% success
- validation crashes stayed at 90% to 92%

This is a classic proxy-metric failure: training curves look less bad, but
the competition-style evaluator does not improve.

## Retention Signals

The beta=0 control arm did not perform teacher retention:

- `losses/teacher_kl`: 0
- `retention/sampled_batch_size`: 0
- `retention/teacher_agreement`: NaN
- teacher action MSE is not meaningful

This is expected for beta=0, but it means the run cannot validate the v27
teacher-retention hypothesis.

## Recommendation

- Do not use the analyzer's simple gate-reward scaling recommendation as the
  next action.
- Do not continue beta=0.
- Do not start beta=0.03 or beta=0.10 until retention dataset loading,
  frozen teacher inference, dual teacher/student observation paths, and real
  KL logging are implemented and reviewed.
- In the first nonzero-beta sanity run, W&B must show nonzero sampled retention
  batches and finite teacher KL/agreement metrics before any 5M screen is
  trusted.
