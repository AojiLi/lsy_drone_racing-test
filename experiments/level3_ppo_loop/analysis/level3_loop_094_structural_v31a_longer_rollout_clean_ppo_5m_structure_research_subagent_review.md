# Loop094 Structure/Research Review

Verdict: follow v31a with implementation work, not immediate maturation or
rejection.

v31a is a useful baseline improvement but only weakly promising:

- best checkpoint: 4M;
- success: `19/100`;
- mean successful time: `6.875789473684211s`;
- crash: `81/100`;
- mean gates: `1.55`.

It beats loop093 by `+2pp` success and meets the time target among successful
episodes, but it does not improve mean gates, misses the stronger screen
(`>=20/100` success or `>=1.60` mean gates), and remains far from the final
`config/level3.toml` target.

Framework fit:

- v31a completed the clean longer-rollout feed-forward PPO baseline stage;
- `256 envs x 128 steps` should remain the clean baseline geometry for the next
  structural lane;
- the remaining failure looks like gate acquisition, value-signal quality, and
  training-distribution weakness, not speed tuning or track geometry.

Recommended next named structural lane:

`v31b_obs_return_norm_clean_ppo_5m`

Scope:

- implement actor observation RunningMeanStd;
- implement critic/return running scale and checkpoint metadata;
- keep v5 observations;
- keep `256 x 128` rollout geometry;
- keep loop052 reward numbers initially;
- hard-evaluate only on `config/level3.toml` validation_unseen seeds 101-200;
- use v31a 4M as the reference checkpoint if compatibility is clean, otherwise
  fall back to loop052 final.

Do not accept the analyzer reward-number recommendation as the next main move
yet. Reward numbers come after observation/value normalization makes PPO updates
and value targets more trustworthy.
