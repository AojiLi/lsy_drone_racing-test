# Loop122 Subagent Reviews: v51 Planner-Guidance Observation PPO256

Trial:
`level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_analysis.md`

Hard-eval target:
unchanged `config/level3.toml`, validation_unseen seeds `101-200`.

## Evaluator Metrics Review

- Target was not met.
- Best loop122 checkpoint was `10M`:
  `18%` success, `1.42` mean gates, `81%` crash, `1%` timeout,
  and `6.991s` mean successful time.
- The best mean-gates checkpoint was `20M`:
  `16%` success, `1.57` mean gates, `84%` crash, and `7.013s`
  mean successful time.
- Final fell to `12%` success, `1.42` mean gates, and `88%` crash.
- v51 missed all promotion gates from the v51 decision packet:
  no checkpoint reached `>=25%` success, `>=1.75` mean gates, or `<=75%`
  crash.
- Failure remains contact/bounds dominated. At the best 10M checkpoint:
  `79` contact, `2` bounds, `1` timeout, and `18` finishes. Failures by
  target gate were gate0 `37%`, gate1 `24%`, gate2 `19%`, and gate3 `2%`.
- Seed coverage is unstable rather than clearly expanded: the 10M checkpoint
  gains some validation seeds but loses old frontier seeds.

Recommended direction:
do not mature v51 as-is to 60M. Hold for planner-feature diagnostics or launch
a new named structural lane only after diagnostics.

## W&B / PPO Diagnostics Review

- PPO update pressure was active. v51 does not look like the v49 near-zero
  update failure.
- W&B tail metrics:
  `approx_kl=0.011704`, `clipfrac=0.055996`, `policy_loss=-0.01481`,
  entropy fell to `1.254311`, and explained variance reached `0.786982`.
- Training reward and reward components improved:
  `train/total_reward=36846.265625`, `train/reward=1072.001343`, and gate
  reward components rose.
- The training signal did not convert into hard-eval progress:
  `race/finished_rate=0.00061`, `race/passed_gate_rate=0.008759`, and
  checkpoint hard-eval success stayed at or below `18%`.
- The checkpoint curve degraded after the early best:
  `10%`, `18%`, `13%`, `16%`, `14%`, `12%` success from 5M through final.

Recommended direction:
do not tune PPO mechanics first. KL, clip fraction, entropy, SPS, and explained
variance are healthy enough that learning-rate, entropy, target-KL, or update
epoch changes are not the main diagnosis. The failure is gate/finish conversion.

## Structure / Research Synthesis Review

- v51 failed more like an observation/planner-feature integration problem, with
  a secondary training-structure concern, not a reward-number problem.
- Planner guidance did not open new gate progress; it underperformed its own
  warm-start source, loop110/v39 3M:
  `21%` success, `1.64` mean gates, `79%` crash, and `6.756s`.
- v51 also did not beat loop121/v50: both peaked at `18%` success, but v51 had
  lower mean gates (`1.42` vs `1.56`) and slightly worse crash (`81%` vs
  `80%`).
- Reward is less likely to be primary because v51 kept the v39/v50
  gate-acquisition reward family and successful episodes are already fast
  enough. The hard problem is coverage and gate acquisition.

Recommended direction:
choose `hold_for_more_analysis` and run planner-feature diagnostics before any
next train/evaluate chunk. If diagnostics are clean, consider a new named v52
structural lane such as
`v52_planner_guidance_feature_norm_ablation_ppo256_from_loop110_3m`.

Required diagnostics before any v52 training:

- verify checkpoint metadata has planner guidance enabled and used at inference;
- inspect train/eval parity for the planner-guidance slice;
- inspect planner feature distributions and ranges on validation seeds;
- compare v51 success/loss seed sets against loop110/v39 3M;
- check whether appended planner input weights moved meaningfully from zero.

## Main-Agent Synthesis

Decision direction:
`hold_for_more_analysis`.

Rationale:
v51 was a reasonable structural test, but its hard-eval result did not beat the
frontier and did not satisfy the v51 promotion gate. PPO learning dynamics were
active, so the immediate issue is not an under-updating policy. The added
planner-guidance observation did not convert into reliable gate acquisition and
may be poorly scaled, weakly used, or mismatched between train/eval or
feature intent and policy learning.

The next action should not be another blind 30M/60M continuation and should not
be the analyzer's narrow reward-number suggestion. The safe next move is a
diagnostic hold focused on planner-feature semantics, metadata, parity, ranges,
seed coverage, and whether the appended input weights actually learned.

Guardrails:
do not edit `config/level3.toml`; do not use planner as MPC, action override,
safety shield, static seed replay, or fallback controller; hard-eval all future
candidates on unchanged `config/level3.toml`.
