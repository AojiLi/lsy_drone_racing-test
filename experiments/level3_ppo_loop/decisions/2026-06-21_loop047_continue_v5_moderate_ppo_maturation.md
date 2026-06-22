# Main-Agent Decision After loop047

Date: 2026-06-21

## Trial

- Trial id:
  `level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m`

Best loop047 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_final.ckpt`

Hard-eval metrics:

- Success rate: `0.15`
- Mean successful time: `6.32s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.25`
- Target met: `false`

Current global best remains loop020:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`,
crash `0.85`, and mean gates `1.45`.

## Subagent Findings

- `evaluator_metrics` recommended `continue_same_hypothesis`.
  It noted that loop047 ties loop020 on success and crash and is slightly
  faster on successful runs, but is worse on mean gates. Continuation should be
  narrow and should start from loop047 final while preserving loop020 as the
  rollback/global best.
- `wandb_ppo_diagnostics` recommended
  `change_reward_or_training_numbers`. W&B reward rose strongly, but
  `passed_gate_rate`, `finished_rate`, and gate-plane conversion stayed weak.
  PPO was stable, with mild late under-updating rather than numeric
  instability.
- `structure_research_synthesis` recommended
  `continue_same_hypothesis`. It found no stronger launch-ready structural lane
  than one short maturation of loop047, and warned against immediately applying
  the analyzer's generic gate-acquisition reward retune because similar
  directions have regressed from loop020 before.

## Main-Agent Decision

Selected decision:

`continue_same_hypothesis`

## Rationale

loop047 is not a breakthrough, but it is a valid short maturation candidate.

Reasons to continue once:

- It recovered loop020-level success (`0.15`) and crash (`0.85`).
- It reduced command saturation relative to loop020:
  command tilt over-limit `0.386` vs loop020 `0.580`.
- It is materially better than the rejected loop046/v7 stability retune.
- The Level2 step-curve policy says 30M is screening/debug evidence, not a
  final success-rate judgment, when a branch has non-zero hard-eval success.

Reasons to keep this continuation narrow:

- It did not improve over loop020 on the main frontier.
- Mean gates are lower than loop020: `1.25` vs `1.45`.
- W&B reward gains did not clearly convert into pass/finish progress.
- The next run must prove that safer action behavior can mature into gate
  progress, not just higher shaped reward.

Therefore the next move is one 30M continuation from loop047 final, using the
same v5 observation layout, same legacy reward values, same PPO/training values,
and same controller/action settings. This brings the lane to a 60M-style
maturation point before rejecting or changing it.

## Next Run

Lane name:

`v5_loop047_moderate_ppo_soft_damping_maturation_60m`

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_final.ckpt`

Scope:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure:
  `legacy_staged`
- Keep latest loop047 reward/training/controller numbers unchanged.
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- Use W&B project `ADR-PPO-Racing-Level3`.

## Promotion And Rollback

Promote the lane only if a checkpoint beats loop020 on at least one main
frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45` and crash no worse than
  `0.85`; or
- success `0.15` with materially lower crash and no gate regression.

Reject or hold this exact lane if:

- all evaluated checkpoints stay `<=0.10` success;
- all evaluated checkpoints stay below `1.25` mean gates;
- late checkpoints collapse to `0.00` success or `1.00` crash;
- W&B reward rises while `passed_gate_rate`, `finished_rate`, and
  gate-plane conversion stay flat;
- the 60M-style continuation still ties success but stays below loop020 mean
  gates.

If rejected after this continuation, do not keep extending this exact lane.
Return to loop020 or the best hard-eval checkpoint as the anchor for a new
reward/controller decision packet.

## Required Dry-Run Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --keep-latest-params \
  --allow-step-curve-maturation \
  --proposal-name v5_loop047_moderate_ppo_soft_damping_maturation_60m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop047_continue_v5_moderate_ppo_maturation.md
```

If the dry-run is clean, run the same command without `--dry-run`.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not modify `notebooks/train_level3_ppo.ipynb`.
- Do not treat W&B reward as acceptance.
- Do not continue to 90M unless this 60M-style continuation improves the
  hard-eval frontier or a new decision packet explicitly justifies the budget.
