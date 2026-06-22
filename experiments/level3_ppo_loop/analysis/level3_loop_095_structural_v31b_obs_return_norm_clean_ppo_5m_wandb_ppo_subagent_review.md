# Loop095 v31b W&B/PPO Diagnostics Review

## Key Finding

`v31b_obs_return_norm_clean_ppo_5m` made the critic/value scale numerically
cleaner, but the normalized training signal did not convert into evaluator
progress. PPO did not collapse, yet hard eval regressed sharply from loop094:
best v31b checkpoint is 1M with `0%` success, `96%` crash, `4%` timeout, and
`0.0` mean gates.

## Evidence

W&B was available for run
`level3_loop_095_structural_v31b_obs_return_norm_clean_ppo_5m`.

Training curves were mixed: `train/total_reward` improved from `-87658.8` to
`-65157.1`, while `train/reward` worsened from `-106.95` to `-169.91` with tail
mean `-185.36`.

Normalization was enabled in state/training params: `obs_norm_enabled=True`,
`return_norm_enabled=True`, both clip `10.0`, from-scratch warm start. However,
no explicit W&B norm-stat series were present in the analyzer metric set, such
as RMS mean/variance, clipping rate, or normalized return scale. Downstream
evidence is value-side only: `value_loss` fell to `0.206`, while
`explained_variance` remained weak at `0.127` last, max `0.261`.

PPO update pressure stayed low and non-explosive: `approx_kl=0.00431` versus
`target_kl=0.03`, `clipfrac=0.00329`, `policy_loss=-0.00360`. Entropy rose from
`0.594` to `0.763`, so this was not entropy collapse.

Reward components show approach-shaping motion but no event conversion:
`gate_stage_progress` improved to `0.009`, `gate_axis_progress` to `0.0048`,
`wrong_side` became less negative, and gate distance decreased. But
`finish_bonus`, `gate_back`, and tail `gate_bonus` were all `0`;
`race/passed_gate_rate=0`, `race/finished_rate=0`, and
`race/gate_pass_hit_rate=0`.

Hard evaluator conversion failed at every checkpoint. Across 1M, 2M, 3M, 4M,
and final: success stayed `0%`; mean gates stayed `0.0` except final `0.01`;
crash rate was `96-100%`. Failures were almost entirely at gate 0, with final
showing only one episode reaching gate 1.

## Diagnosis

This is `hold_plateau_no_conversion`. Observation/return normalization improved
value-loss scale, but it did not produce gate acquisition. The hard-eval
behavior looks like low-conversion/no-gate policy behavior rather than PPO
numerical instability.

Do not tune PPO hyperparameters from this run alone. The KL/clip/entropy profile
is diagnostic, not acceptance evidence.

## Recommendation

Do not continue v31b as-is. Hold for a main-agent decision packet and require
either a normalization instrumentation/debug hypothesis or a new named
structural lane. A next v31b-like run should log explicit normalization health
metrics before relying on W&B reward/value curves.

Rollback reference is loop094 4M, the current state best.
