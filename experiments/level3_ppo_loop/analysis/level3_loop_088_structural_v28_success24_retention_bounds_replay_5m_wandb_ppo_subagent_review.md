# Loop088 W&B/PPO Diagnostics Review

Verdict: do not accept this branch as successful. Hard eval improved slightly
but remains far below target: 19% success versus >=60%, with 81% crash rate.
Mean successful time is good at 6.846s, but it only applies to the small
successful subset.

PPO stability:

- approx KL around 0.0043
- clip fraction around 0.01
- entropy remains high but gently declining
- explained variance around 0.75
- no evidence supports silent PPO hyperparameter tuning
- race W&B metrics are mostly flat: finish rate, passed-gate rate, crash rate,
  and gate stage did not meaningfully turn upward

Teacher retention:

- teacher KL fell from 1.406 to 1.042
- teacher action MSE fell from 0.0212 to 0.0103
- teacher agreement rose from 0.816 to 0.879, with tail mean 0.868
- sampled retention batch size stayed 512

Hard-eval conversion:

Reward/retention did not materially convert to hard eval. Best checkpoint
gained only +0.02 success rate and +0.07 mean gates versus the prior evaluated
trial, while crashes remain dominant. This is still a gate-acquisition failure,
not a speed-optimization problem.

Recommended next action:

Choose `change_reward_or_training_numbers`, focused on stronger gate
acquisition, consistent with the analyzer's proposed gate-stage, gate-axis,
front/back/finish reward adjustment. Do not launch training until the main
agent writes a decision packet, then run exactly one bounded chunk with both
`--analysis-packet` and `--approved-hypothesis-packet`.
