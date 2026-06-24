# Loop120 Subagent Reviews: V49 Hidden512 45M To 60M Recovery

Trial:
`level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_analysis.md`

Hard eval:
unchanged `config/level3.toml`, `validation_unseen` seeds 101-200.

## evaluator_metrics

Key finding: v49 recovery did not preserve or expand the old Level3 frontier.
The best loop120 checkpoint was the recovery 5M checkpoint with `15%` success,
`1.50` mean gates, `85%` crash, and `6.741s` mean successful time.

Evidence:

- recovery 5M: `15%` success, `1.50` mean gates, `85%` crash;
- recovery 10M: `14%` success, `1.46` mean gates, `86%` crash;
- final: `13%` success, `1.41` mean gates, `87%` crash;
- no timeout problem; failures remain contact/bounds dominated;
- the old frontier remains loop107/v37 1M at `21%` success and `1.66` mean
  gates, with loop110/v39 3M as the best feed-forward start.

Recommended next action: do not continue v49 as-is toward 90M/120M. Stay
inside the hidden512 family, but change the next axis.

## wandb_ppo_diagnostics

Key finding: training did not convert into evaluator progress, and late PPO
movement was almost frozen.

Evidence:

- `train/total_reward` and `train/reward` worsened;
- gate bonus and gate-stage signals did not convert into hard-eval success;
- `losses/approx_kl` ended around `0.000002`;
- `losses/clipfrac` stayed `0.0`;
- `losses/policy_loss` was near zero;
- entropy rose to about `5.38`;
- value loss stayed high while explained variance was only diagnostic, not a
  success signal;
- W&B race metrics stayed flat/high-crash.

Recommended next action: do not keep the same low learning rate plus annealing
schedule. If the next lane remains hidden512, make it a named PPO/training
number follow-up with explicit provenance.

## structure_research_synthesis

Key finding: loop120 is not evidence that hidden512 should be abandoned, but it
is evidence against same-hypothesis maturation.

Evidence:

- v49 still has non-zero gate progress, so there is no obvious architecture
  wiring failure;
- the 60M read underperformed and drifted downward;
- the failure signature is not "too slow"; successful runs were already under
  `7.0s`;
- the bottleneck remains conversion and crash control across multiple gates.

Recommended next action: launch one targeted hidden512 update-pressure lane
before moving to hidden512 observation, memory, or curriculum. Keep the track,
v5 observation, and deployment controller unchanged for this follow-up.

## Shared Conclusion

All three reviewers reject continuing v49 as-is. The main decision should not
mark hidden512 dead from one evaluated family run, because the v49 plan
explicitly required more than one hidden512-family axis before rejecting the
capacity family. The next step should be a named hidden512 follow-up that
addresses the specific W&B diagnosis: weak PPO update pressure and high
entropy, with hard eval remaining on unchanged `config/level3.toml`.
