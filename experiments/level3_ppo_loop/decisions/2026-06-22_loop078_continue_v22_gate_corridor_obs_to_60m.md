# Loop078 Decision: Continue V22 Gate-Corridor Observation To 60M

Decision: continue_same_hypothesis

Pending gate resolved for:

- trial_id:
  `level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m`
- analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_analysis.md`
- analysis json:
  `experiments/level3_ppo_loop/analysis/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_analysis.json`

## Verdict

Continue the same v22 hypothesis. Do not apply the analyzer's repeated
v21-style gate-reward increase yet. Do not change PPO/training numbers,
controller settings, reward structure, observation layout, or the Level3 track.

## Evidence

Best loop078 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_final.ckpt`

Hard eval on unchanged `config/level3_dr.toml`:

- success rate: 0.25
- mean successful time: 8.048s
- crash rate: 0.75
- timeout rate: 0.00
- mean gates: 2.05
- target met: false

Comparison:

- vs loop071 20M: same success and crash, slightly better mean gates
  (`2.05` vs `2.00`) and faster successful time (`8.048s` vs `8.524s`)
- vs loop069 global best: better success (`0.25` vs `0.20`), better mean gates
  (`2.05` vs `1.45`), lower crash (`0.75` vs `0.80`), but slower successful
  time (`8.048s` vs `6.675s`)

Success seeds shifted to `[4, 9, 12, 18, 19]`, showing partial retention plus
new successes. This is not enough for the target, but it satisfies the v22
promotion rule and is a better maturation candidate than another immediate
reward-number change.

## Reviewer Consensus

Evaluator metrics:

- Mature v22.
- Use hard-eval maturation evidence to test whether v22 can exceed the 0.25
  frontier, keep mean gates above 2.05, reduce crash below 0.75, and pull time
  toward 7.0s.

W&B/PPO diagnostics:

- PPO is stable: low/flat KL and clip fraction, healthy entropy, steady
  explained variance.
- Do not tune learning rate, entropy coefficient, target KL, minibatches,
  epochs, hidden size, or observation count from this evidence.

Structure/research synthesis:

- Continue v22; do not retune reward yet.
- Earlier v21 gate-reward pressure worsened obstacle/frame crashes, so the
  repeated gate-acquisition recommendation is not the next move.

## Next Lane

`v22_gate_corridor_obs_maturation_from_loop078_final_to_60m`

Contract:

- initial checkpoint: loop078 final
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- PPO/controller/reward numbers: unchanged from loop078/v22
- track generator profile: `default`
- horizon: 40M additional steps with 5M checkpoint evaluation
- use step-curve maturation because the initial checkpoint has promising
  hard-eval evidence

## Promotion And Rollback

Promote or continue toward 90M if a milestone reaches one of:

- success `> 0.25`
- mean gates `> 2.05` with crash `<= 0.75`
- crash `< 0.75` while keeping success `>= 0.25`
- mean successful time approaches `<= 7.0s` without losing success/gates

Hold for v22-specific trace diagnostics if the next chunk falls below:

- success `< 0.20`, or
- mean gates `< 2.00`, or
- crash `> 0.80`

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v22_gate_corridor_obs_maturation_from_loop078_final_to_60m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop078_continue_v22_gate_corridor_obs_to_60m.md
```
