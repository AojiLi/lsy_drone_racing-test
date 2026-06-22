# Loop089 W&B/PPO Diagnostics Review

Verdict: `hold_plateau_no_conversion`.

Target was not met: best hard eval is 18% success, 7.002s mean successful time,
82% crash rate, and 1.49 mean gates.

PPO stability:

- PPO appears stable enough; no PPO instability diagnosis
- approx KL is low/flat around 0.0037
- clip fraction is very low around 0.006
- entropy remains high around 5.61 with slight decline
- explained variance improved to about 0.72
- value loss is trending down, though still large

Teacher retention:

- teacher KL dropped from 1.054 to 0.754
- teacher action MSE improved from 0.0110 to 0.0076
- teacher agreement rose from 0.875 to about 0.905 last / 0.917 tail mean
- sampled batch size stayed stable at 512

Gate reward adjustment:

The adjustment harmed, or at least failed, hard-eval conversion. Versus the
prior evaluated trial, success fell by 1pp, mean gates fell by 0.08, crash
rate rose by 1pp, and successful runs became about 0.156s slower. W&B train
reward improved, but race passed-gate, finished-rate, crash-rate, and
gate-stage signals stayed flat, so reward gains did not convert.

Recommended next action:

Do not launch another training chunk yet. Choose `hold_for_more_analysis` or
write an explicit `change_reward_or_training_numbers` packet that abandons this
gate-conversion adjustment. No automatic reward move should run without an
approved decision packet.
