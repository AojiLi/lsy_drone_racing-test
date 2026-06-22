# Loop089 Decision: Reject Gate-Conversion Adjustment, Hold For Behavior Diagnostic

Decision: `hold_for_more_analysis`

## Verdict

Reject loop089 as a continuation candidate.

Do not continue the loop089 reward-number direction, do not mature it to 60M,
and do not launch another automatic reward-number move.

This is a hold for targeted analysis, not a full rejection of the v28
data-correction idea. The next work is to compare loop088 4M versus loop089 2M
behavior and design a new named lane only after that diagnostic is written.

## Evidence

Best current global checkpoint remains loop052 final:

- validation success: 0.20
- crash: 0.80
- mean gates: 1.47
- mean successful time: 6.858s

Loop088 4M, the v28 pre-adjustment parent:

- validation success: 0.19
- crash: 0.81
- mean gates: 1.57
- mean successful time: 6.846s

Loop089 2M, best checkpoint after gate-conversion reward adjustment:

- validation success: 0.18
- crash: 0.82
- mean gates: 1.49
- mean successful time: 7.002s

Loop089 regressed versus loop088 4M on every hard-eval gate:

- success -1pp
- crash +1pp
- mean gates -0.08
- mean successful time +0.156s

Loop089 also failed the continuation gate from the loop088 decision: no
validation success >=0.20, no crash <=0.80, no mean-gate progress above 1.57,
and no reduction in `bounds_or_ground` failures.

## Subagent Synthesis

Evaluator metrics:

- reject loop089 as a continuation candidate;
- failures remain dominated by `bounds_or_ground`;
- failure by target gate is gate0 34%, gate1 22%, gate2 23%, gate3 3%;
- recommends not continuing the same hypothesis or another automatic
  reward-number tweak.

W&B/PPO diagnostics:

- PPO is stable; no optimizer/PPO instability diagnosis;
- teacher retention is healthier, with teacher KL down and teacher agreement
  around 0.905 last / 0.917 tail mean;
- W&B train reward improved, but passed-gate, finished-rate, crash-rate, and
  gate-stage signals did not convert;
- recommends hold or an explicit packet that abandons the failed reward
  direction.

Structure/research synthesis:

- reject the reward escalation, but do not reject all of v28 yet;
- retention and PPO wiring look healthy;
- the failure is stronger evidence that reward accounting pulled behavior away
  from useful validation conversion;
- before more training, compare loop088 4M and loop089 2M trajectories around
  gate approach and bounds/ground endpoints.

## Rejected Next Actions

- continue loop089;
- mature loop089 to 60M or 90M;
- continue the same reward-number escalation;
- launch another automatic reward-number move from analyzer output alone;
- modify `config/level3_dr.toml`;
- inspect or train on `final_locked` seeds.

## Approved Next Work

Create a behavior diagnostic comparing:

- loop088 4M:
  `lsy_drone_racing/control/checkpoints/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt`
- loop089 2M:
  `lsy_drone_racing/control/checkpoints/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_step_002000000.ckpt`

Use only `dev_seen`, `validation_unseen`, and train-pool diagnostics already
allowed by the loop. Do not use `final_locked` seeds.

The diagnostic should answer:

1. Which loop052/loop088 validation successes were lost by loop089?
2. Which successes were gained?
3. Did loop089 increase centerline error, gate-axis regression, command tilt,
   or bounds/ground endpoints around gate0/gate1?
4. Did stronger reward pressure overfit W&B reward while reducing hard-eval
   gate conversion?
5. What named next lane is safest: revert reward numbers and change data
   replay, add a behavior-cloning/retention variant, or hold for a larger
   structure change?

## Training Gate

No next train/evaluate chunk is approved by this packet.

A future packet may approve training only after the behavior diagnostic is
written and explicitly names the next lane. Hard eval must remain unchanged
`config/level3_dr.toml`, and `final_locked` seeds must remain locked.
