# Loop121 Subagent Reviews: v50 Hidden512 Update Pressure

Trial:
`level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_analysis.md`

Hard-eval target:
unchanged `config/level3.toml`, validation_unseen seeds `101-200`.

## Evaluator Metrics Review

- Target was not met.
- Best loop121 checkpoint was `25M`:
  `18%` success, `1.56` mean gates, `80%` crash, `2%` timeout,
  `6.283s` mean successful time.
- The final checkpoint fell to `15%` success, `1.45` mean gates, and `85%`
  crash.
- The global best remains loop107/v37 1M:
  `21%` success, `1.66` mean gates, `79%` crash, and `7.578s` mean successful
  time.
- v50 improved over loop120 by `+3pp` success, `+0.06` mean gates, and `-5pp`
  crash, but did not expand the frontier. The immediate next move should not be
  another v50 maturation unless a separate decision explicitly chooses that.

## W&B / PPO Diagnostics Review

- v50 did fix the v49 near-zero update-pressure symptom:
  `approx_kl=0.014064`, `clipfrac=0.065216`, `policy_loss=-0.013724`, and
  entropy fell to `0.63339`.
- This update pressure converted only weakly in hard eval:
  loop120 `15%` success / `1.50` mean gates / `85%` crash became loop121
  `18%` success / `1.56` mean gates / `80%` crash at the best checkpoint.
- The milestone curve was unstable:
  `14%`, `17%`, `11%`, `14%`, `18%`, `15%` from 5M through final.
- W&B race signals remained flat enough that the next lane should not be
  another PPO-number tuning loop. For the planner-observation lane, track
  `approx_kl`, `clipfrac`, entropy/action std, value loss, explained variance,
  `race/passed_gate_rate`, `race/finished_rate`, `race/crashed_rate`,
  `race/gate_stage`, and planner-feature validity/scale.

## Structure / Research Synthesis Review

- The next move should be a named structural lane because planner-as-observation
  changes the deployed observation contract and uses planner computation at
  inference.
- Planner guidance is more directly targeted than hidden512/reward-only loops:
  recent trials show success stuck around `18%-21%` while successful episodes
  are already fast enough. The bottleneck is route intent, gate/corridor choice,
  and obstacle geometry, not raw speed.
- PPO256 is plausible because the planner channels provide local route intent,
  reducing the burden on the policy network. The PPO actor must remain the only
  action-producing controller.
- Guardrails:
  do not edit `config/level3.toml`; do not use planner as MPC, action override,
  safety shield, static seed replay, or fallback controller; hard-eval all
  candidates on unchanged `config/level3.toml`.

## Main-Agent Synthesis

Decision direction: reject v50 as the immediate next move and launch
`v51_planner_guidance_obs_ppo256_from_loop110_3m`.

Rationale:
v50 repaired PPO update mechanics, but it did not repair Level3 hard-eval
behavior enough to justify another same-family run. Planner-guidance observation
directly addresses the suspected missing route-intent signal while preserving
the action contract:

```text
Level3 observation/history + deterministic planner-guidance features
  -> PPO Actor
  -> roll/pitch/yaw/thrust
```

The planner is allowed only as observation computation at inference. It does not
produce actions, replace the actor, modify the track, replay seeds, or act as a
safety shield.
