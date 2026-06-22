# Loop094 W&B/PPO Diagnostics Review

Verdict: PPO is stable but update pressure is very low. Longer rollout weakly
improved hard-eval conversion, but not enough to justify unchanged
continuation as the main move.

Evidence:

- `approx_kl=0.000873`;
- `clipfrac=0.000006`;
- entropy `4.18`;
- explained variance `0.756`;
- value loss `252.6`;
- race metrics remain tiny: passed gate rate `0.005859`, finished rate
  `0.000153`, gate stage `0.068054`;
- teacher retention is inactive.

Hard-eval conversion:

- success improved only `+0.02`;
- crash improved only `-0.02`;
- mean successful time improved by about `0.17s`;
- mean gates stayed flat at `1.55`.

Warning signs:

- training reward worsened late in the run;
- policy loss, KL, and clip fraction suggest the policy is barely moving;
- no evidence of destructive PPO instability.

Recommended next action:

Choose a training/reward-number change rather than unchanged v31a continuation
if staying inside the current trainer. The analyzer's gate-acquisition
direction is consistent with the low gate progress, but this review does not
override the framework priority that value/observation normalization should be
implemented before reward-number search.

Rollback condition:

Do not optimize speed or alter `config/level3.toml`. If the next lane keeps
showing near-zero KL/clip fraction and no evaluator progress, diagnose update
pressure and value target scale before longer runs.
