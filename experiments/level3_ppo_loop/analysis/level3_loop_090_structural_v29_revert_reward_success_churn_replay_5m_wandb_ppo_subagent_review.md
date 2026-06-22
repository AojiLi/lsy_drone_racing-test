# W&B/PPO Diagnostics Review: loop090 v29 Success-Churn Replay

## Key Finding

W&B improved internally, but did not convert to hard eval. Training reward rose,
teacher retention stayed healthy, and PPO KL/clip metrics were not unstable.
The hard evaluator still fell to 0.14 success, 0.86 crash, and 1.39 mean gates.

## Training Signals

- `train/total_reward`: last `-29090.34`, tail mean `-27607.97`, trend up
- `train/reward`: last `-30.38`, tail mean `-123.55`, trend up
- hard-eval delta vs previous trial: success `-0.04`, mean gates `-0.10`
- best hard-eval successful time: 6.72s

The time metric is not the immediate blocker; success and crash are.

## Teacher-Retention Diagnostics

Teacher-retention diagnostics are valid and healthy:

- `losses/teacher_kl`: `1.033 -> 0.710`
- `losses/teacher_action_mse`: `0.0122 -> 0.0104`
- `retention/teacher_agreement`: `0.861 -> 0.892`, tail mean `0.902`
- `retention/sampled_batch_size`: fixed at `512`

This rules out the earlier failure mode where nonzero beta was not actually
using a real retention batch.

## PPO Diagnostics

No obvious optimizer blow-up:

- `losses/approx_kl`: flat around `0.004`
- `losses/clipfrac`: flat around `0.006`
- `losses/entropy`: still high around `5.49`
- `losses/explained_variance`: flat around `0.72`
- SPS increased during the run

The main risks are conversion failure and crash dominance, not PPO KL/clip
instability. `losses/value_loss` rose at the end, but this is not enough by
itself to explain the hard-eval regression.

## Recommendation

Diagnostics support `hold_for_more_analysis`.

Do not continue the reward-churn replay lane simply because W&B reward improved.
Any next move should require a main-agent decision packet and either an explicit
reward/training-number hypothesis or a new named structural lane.
