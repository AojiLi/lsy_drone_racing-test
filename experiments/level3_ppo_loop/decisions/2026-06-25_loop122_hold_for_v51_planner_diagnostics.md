# Decision: Hold Loop122 For V51 Planner Diagnostics

Decision: `hold_for_more_analysis`

Trial resolved:
`level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_analysis.md`

Subagent review packet:
`experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_subagent_reviews.md`

Research packet:
`experiments/level3_ppo_loop/research/2026-06-24_level3_v51_planner_guidance_obs_ppo256_plan.md`

## Decision

Hold. Do not launch another train/evaluate chunk yet.

Do not continue v51 as-is toward `60M` or `90M`. Do not accept the analyzer's
reward-number command as the next move. Before any v52 or v51-family training,
run targeted planner-feature diagnostics.

## Rationale

v51 tested the approved deployed observation path:

```text
v5 observation/history
+ deterministic planner-guidance observation features
  -> 2x256 Tanh PPO Actor
  -> roll/pitch/yaw/thrust
```

The planner remained observation-only. It did not output actions, override PPO
actions, act as MPC, provide a safety shield, replay seed-specific routes, or
change the race track.

The hard evaluator did not improve:

| checkpoint | success | mean gates | crash | timeout | mean successful time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5M | 10% | 1.35 | 90% | 0% | 6.436s |
| 10M | 18% | 1.42 | 81% | 1% | 6.991s |
| 15M | 13% | 1.48 | 86% | 1% | 5.978s |
| 20M | 16% | 1.57 | 84% | 0% | 7.013s |
| 25M | 14% | 1.43 | 86% | 0% | 6.517s |
| final | 12% | 1.42 | 88% | 0% | 6.368s |

Best by success was the `10M` checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_step_010000000.ckpt`;
- success: `18%`;
- mean gates: `1.42`;
- crash: `81%`;
- timeout: `1%`;
- mean successful time: `6.991s`.

Best by mean gates was the `20M` checkpoint:

- success: `16%`;
- mean gates: `1.57`;
- crash: `84%`;
- mean successful time: `7.013s`.

The global best remains loop107/v37 1M:
`21%` success, `1.66` mean gates, `79%` crash, and `7.578s`.
The feed-forward warm-start source loop110/v39 3M was also better than v51:
`21%` success, `1.64` mean gates, `79%` crash, and `6.756s`.

v51 therefore missed its own promotion gates:

- no checkpoint reached `>=25%` success;
- no checkpoint reached `>=1.75` mean gates;
- no checkpoint reached `<=75%` crash.

PPO update health was not the main blocker:

- `approx_kl=0.011704`;
- `clipfrac=0.055996`;
- `policy_loss=-0.01481`;
- entropy fell to `1.254311`;
- explained variance reached `0.786982`.

Training reward and gate reward components improved, but W&B race conversion
and hard eval did not. This points toward planner-feature semantics, scaling,
usage, or parity rather than another PPO update-pressure experiment.

## Required Diagnostics Before Any Next Training

Run a read-only planner-feature diagnostic packet before launching v52 or any
v51-family continuation:

1. Verify v51 checkpoint metadata records planner guidance enabled and used at
   inference.
2. Verify train/eval observation parity covers the `planner_guidance` slice.
3. Inspect planner feature distributions and ranges on validation seeds,
   especially clipping/saturation and scale relative to v5 features.
4. Compare v51 success/loss seed sets against loop110/v39 3M and loop107/v37
   1M to identify whether planner guidance solved genuinely new seeds or mostly
   reshuffled old ones.
5. Check whether appended planner-channel input weights moved meaningfully from
   zero in the v51 checkpoints.
6. Confirm `config/level3.toml` geometry, gates, obstacles, randomization, and
   validation seed split remain unchanged.

If diagnostics reveal a metadata, parity, scaling, or feature bug, route the
smallest fix through the builder/checker gate before any training.

If diagnostics are clean, the next structural lane should be named explicitly,
for example:

```text
v52_planner_guidance_feature_norm_ablation_ppo256_from_loop110_3m
```

That lane should change planner-feature representation or training integration,
not Level3 track geometry and not planner action control.

## Guardrails

- Do not edit `config/level3.toml` track geometry, gates, obstacles,
  randomization, or validation seed split.
- Do not add planner action output, MPC, waypoint-controller takeover, safety
  shield, static seed replay, or fallback rule controller.
- PPO Actor remains the only action-producing controller.
- Do not launch another train/evaluate chunk until the diagnostic packet is
  written and, if code changes are required, builder/checker approval passes.

## No Next Training Command

This decision intentionally provides no next training command. The next action
is diagnostic analysis, not training.
