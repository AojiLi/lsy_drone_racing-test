# v30 Semantics Audit Completed With Level3 Target Parity

Decision: `hold_for_more_analysis`

Status: v30 semantic fixes and deterministic loop052 baseline/parity on the
final target config are complete. This packet does not launch training.

## Scope

The final Level3 acceptance target is `config/level3.toml`.

`config/level3_dr.toml` remains historical domain-randomized robustness
evidence and a possible training-only robustness config. It is not the final
acceptance target.

## Implemented Semantic Gates

- Finish gate progress is applied before disabled-drone termination, so passing
  the final gate terminates on the same transition.
- Vector autoreset now uses current-step done flags, while preserving
  `final_observation`, `reset_observations`, and `termination_reason` in
  `infos`.
- Finish reward is awarded only on the transition where `target_gate` becomes
  negative.
- `RaceObservation` resets history and `last_action` per completed vector slot.
- Observation delay buffers reset from the true post-reset observation for done
  slots.
- The checkpoint evaluator records environment-provided `termination_reason`
  in episode and summary CSVs; geometry taxonomy remains only an auxiliary
  crash-location guess.

## Verification

Commands run:

```bash
pixi run -e tests python -m py_compile \
  lsy_drone_racing/envs/race_core.py \
  lsy_drone_racing/envs/drone_race.py \
  lsy_drone_racing/envs/multi_drone_race.py \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  scripts/evaluate_level2_selected_ppo.py \
  scripts/level3_ppo_loop.py

pixi run -e tests pytest -q tests/unit/control/test_level3_v30_semantics_audit.py

pixi run -e tests pytest -q \
  tests/unit/control/test_level3_v30_semantics_audit.py \
  tests/unit/envs/test_race_core.py

pixi run -e tests pytest -q \
  tests/integration/test_envs.py -k "vector_envs_randomization"

pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run --max-iterations 1

pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --structural-hypothesis v30_episode_semantics_only_2m \
  --override-state-hold \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_launch_v30_end_to_end_ppo_corrected_action_and_episode_semantics.md
```

Results:

- v30 audit tests: `10 passed`
- v30 audit + race-core unit tests: `31 passed`
- vector randomization integration check: `2 passed`
- dry-run status: `held_by_state_guard`
- v30-A dry-run status: `planned`
- v30-A dry-run initial checkpoint: loop052 final
- v30-A dry-run train config: `level3.toml`
- v30-A dry-run hard eval config: `level3.toml`
- no training launched

## Loop052 Final-Target Baseline

Command:

```bash
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3.toml \
  --seed-file experiments/level3_ppo_loop/seed_manifests/validation_unseen_101_200.txt \
  --seed-split-name validation_unseen \
  --inference-module ppo_level3_inference \
  --failure-taxonomy \
  --out-prefix experiments/level3_ppo_loop/diagnostics/v30_loop052_parity_validation_unseen \
  lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt
```

Repeat command used the same arguments with out-prefix
`experiments/level3_ppo_loop/diagnostics/v30_loop052_parity_validation_unseen_repeat`.

Both runs matched on key summary and episode fields:

- success count: `16 / 100`
- success rate: `0.16`
- crash rate: `0.84`
- timeout rate: `0.00`
- mean gates: `1.43`
- mean successful time: `6.77375s`
- success seeds:
  `106, 109, 112, 123, 124, 134, 152, 155, 160, 166, 167, 182, 184, 185, 187, 199`
- endpoint classes: `{"bounds_or_ground": 84, "success": 16}`
- termination reasons: `{"contact": 84, "finish": 16}`

The `state.json` final-target `best` and `best_validation` entries now point to
this `level3.toml` baseline. The previous 20% `level3_dr.toml` loop052 result
is retained only under DR robustness history fields.

## Next Allowed Work

Training remains held until the next command explicitly uses an approved named
lane. The natural next lane is the already approved v30 corrected-semantics
screen, starting from loop052 final and hard-evaluating on `config/level3.toml`.

Do not modify `config/level3.toml`.
