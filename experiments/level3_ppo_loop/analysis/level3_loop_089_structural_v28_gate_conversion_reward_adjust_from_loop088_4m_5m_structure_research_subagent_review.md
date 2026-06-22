# Loop089 Structure/Research Review

Verdict: reject loop089's gate-conversion reward adjustment, but do not treat
this as a full rejection of v28.

Gate reward adjustment:

Reject. It worsened the loop088 4M anchor:

- validation success fell from 19% to 18%
- crash rose from 81% to 82%
- mean gates fell from 1.57 to 1.49
- mean successful time drifted just above target at 7.002s

W&B reward improved, but gate/finish behavior stayed flat or worsened, so the
reward accounting did not convert.

Next action:

Choose `hold_for_more_analysis`. Do not continue v28 unchanged immediately, and
do not launch another reward-number move. The loop088 stop/continue gate fired:
below 20% success, crash above 80%, and no gate-progress improvement.

Structural read:

Retention and PPO wiring look healthy: teacher KL is down, teacher agreement is
high, and PPO metrics are stable. The failure is not strong evidence for
optimizer/controller collapse. It is stronger evidence that the gate-pressure
reward adjustment pulled behavior away from useful validation conversion.

Safest next hypothesis:

v28's data-correction idea may still be viable, but loop089's reward-number
escalation is harmful or non-converting. Before any training, compare loop088
4M versus loop089 2M trajectories around gate approach, `bounds_or_ground`
endpoints, and gate0/gate1 failures. If training resumes, it should be under a
new explicit packet that reverts the failed reward adjustment and tests a named
data/behavior-conversion lane, with hard eval still on `config/level3_dr.toml`
and no `final_locked` seeds.
