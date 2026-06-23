# Level3 Loop117/V47 Subagent Reviews

Trial: `level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m_analysis.md`

Hard eval config: unchanged `config/level3.toml`

## Evaluator Metrics

Key finding: loop117/v47 is not promising enough to mature as-is. Its best
hard-eval checkpoint was 3M, but it only reached `20%` success, below the
global loop107/v37 1M frontier of `21%`.

Evidence:

- Best v47 checkpoint: `20%` success, `1.58` mean gates, `7.064s` mean
  successful time, `80%` crash, `0%` timeout.
- Mean gates are below loop107/v37 1M (`1.66`) and loop116/v45 best (`1.60`).
- Failures are still contact/bounds dominated, with target-gate failures
  concentrated at gate 0 (`34%`) and gate 2 (`26%`).
- Seed churn remains high. Only seeds `[120, 182, 184, 185]` succeeded across
  all loop117 checkpoints; the best v47 checkpoint gained some seeds but lost
  old frontier seeds.

Recommended action: do not continue v47. Reject maturation unless a future
override beats `21%` success or clearly improves mean gates above `1.66`
without worse crash/tilt.

## W&B/PPO Diagnostics

Key finding: teacher retention was active and PPO did not blow up, but train
signals did not convert into hard-eval progress.

Evidence:

- Retention batch size stayed at `512`.
- Teacher KL improved from `0.049981` to `0.044482`.
- Teacher action MSE improved from `0.011354` to `0.010212`.
- Teacher agreement improved from `0.871606` to `0.890039`.
- PPO looked stable but under-active: approx KL fell to `0.000007`, clipfrac to
  `0.0`, entropy stayed near `4.49`, and explained variance stayed near
  `0.757`.
- Training reward worsened, with `train/total_reward` moving from about
  `-509` to `-3831`.
- W&B race metrics did not improve: passed-gate rate, finished rate, and gate
  stage all stayed flat or declined.

Recommended action: do not tune PPO numerics silently and do not continue v47
retention. Any next run needs a new decision packet.

## Structure/Research Synthesis

Key finding: v47 rejects residual-frontier retention as the immediate next
lever. The failure points more toward a contact/gate-conversion bottleneck than
to teacher extraction, memory wiring, or retention activation.

Evidence:

- v46 preflight already proved residual-GRU teacher action extraction parity.
- v47 retention metrics were healthy, so the failure is not "retention not
  wired."
- The best v47 hard eval stayed at `20%` success and `1.58` mean gates.
- Failures remained contact-heavy, mainly gate 0 and gate 2.

Recommended next structural direction:
`v48_v5_contact_conversion_reward_structure_from_loop110_3m`.

This lane should start from loop110/v39 3M, keep the deployed v5 MLP Actor and
unchanged `config/level3.toml`, drop teacher retention, and test a bounded
decoupled contact/conversion reward-structure screen around gate-frame,
wrong-side, and missed-gate pressure.

Rollback condition: reject v48 if success stays `<=21%`, mean gates stay
`<=1.66`, crash remains around `79%-80%+`, or reduced gate-frame/contact
pressure simply lowers gate acquisition.
