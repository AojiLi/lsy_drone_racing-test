# W&B/PPO Diagnostics Review: loop087

Verdict: PPO is stable and the beta=0.10 teacher-retention loss is active, but
the run still does not convert into hard-eval reliability. Do not continue this
exact v27 beta sweep as-is.

## Evidence

- Retention worked locally:
  - `teacher_kl`: 2.1588 -> 1.4206
  - `teacher_action_mse`: 0.1459 -> 0.0182
  - `teacher_agreement`: 0.6189 -> 0.8351
  - `sampled_batch_size`: 512 throughout
- PPO looks healthy:
  - `approx_kl` last about 0.00405 versus `target_kl=0.03`
  - `clipfrac` last about 0.0107
  - entropy drifted only from about 6.51 to 6.32
  - explained variance stayed usable around 0.78
  - value loss did not explode
- Training proxies improved somewhat, but not decisively:
  - total reward improved
  - gate distance fell
  - gate/stage proxies moved
  - W&B `finished_rate` remained near zero
  - gate progress stayed low/flat
- Hard eval failed the real gate:
  - validation final success: 0.17
  - crash: 0.83
  - mean gates: 1.50
  - mean successful time: 6.991s

This is below both the competition target and the loop052 validation anchor
of 0.20 success and 0.80 crash.

## Recommendation

Recommended next action: `hold_for_more_analysis`.

Do not continue beta=0.10, do not mature this lane to 60M, and do not treat the
analyzer's generic gate-reward scaling command as sufficient. The failure is
not PPO instability. It is a conversion failure between retained teacher
behavior/training proxies and hard Level3 success.

The next training, if any, should be a named structural/data or reward-structure
lane after a main-agent decision packet, with rollback if validation success
stays below the loop052 anchor or teacher agreement drops below 0.80.
