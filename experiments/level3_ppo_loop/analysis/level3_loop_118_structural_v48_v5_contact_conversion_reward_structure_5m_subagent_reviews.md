# Loop118 V48 Subagent Reviews

Trial:
`level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_analysis.md`

## Evaluator Metrics

Reject v48 as-is. No checkpoint is promising enough to mature.

- Best checkpoint: `1M`
- Success rate: `16%`
- Mean gates: `1.50`
- Crash rate: `84%`
- Mean successful time: `6.516s`

This is worse than loop110/v39 3M and the global loop107/v37 1M frontier,
both of which reached `21%` success with lower crash. All loop118 milestones
stayed between `10%` and `16%` success, with crash between `84%` and `90%`.
The lower successful time is not useful because too few episodes finish.

Recommendation: do not continue v48, do not mature it, and do not start future
work from loop118 final.

## W&B / PPO Diagnostics

v48 did not convert its contact/reward changes into evaluator progress.

- `passed_gate_rate` decreased versus the previous retention lane.
- `finished_rate` decreased.
- `gate_axis_x` worsened.
- Wrong-side and missed-gate proxies improved slightly, but that did not
  produce more passes or finishes.
- PPO did not catastrophically explode: KL and clip fraction were very low,
  entropy rose, explained variance stayed finite, and SPS was healthy.

The failure mode is therefore not "training crashed"; it is that the new reward
pressure optimized local proxies while reducing hard-eval gate acquisition.

Recommendation: reject v48 and avoid another automatic contact-reward tweak.

## Structure / Research Synthesis

v48 shows that more contact/conversion reward shaping is not the next best
lever. The current corrected Level3 loop has many 2x256 MLP lanes stuck near
`19%` to `21%` success, while retention and contact-reward screens did not
expand the frontier.

The next structural move should create a new capacity baseline rather than
keep tuning the same 2x256 reward structure. The proposed next lane is:

`v49_v5_hidden512_mlp_warmstart_from_loop110_3m`

It should:

- start from loop110/v39 3M;
- keep v5 observation;
- keep v39 reward numbers;
- expand the 2-layer Tanh Actor/Critic from hidden_dim `256` to `512`;
- use explicit block-copy warm-start via `allow_hidden_dim_warmstart`;
- hard-evaluate only on unchanged `config/level3.toml`;
- become the baseline for later hidden512 reward, observation, curriculum, or
  GRU follow-up lanes if it does not degrade.

Rollback if the best milestone falls below `18%` success, below `1.55` mean
gates, above `83%` crash, or if W&B gate/finish conversion weakens further.
