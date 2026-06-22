---
name: level3-ppo-loop
description: Use when training, evaluating, or tuning the Level3 PPO drone-racing loop for final evaluation on config/level3.toml with the target of <=7.0s mean successful time and >=60% success.
---

# Level3 PPO Loop

Use this workflow for Level3 PPO train/evaluate/tune work.

## Contract

- Target config: `config/level3.toml`.
- Target gate: success rate `>= 0.60` and mean successful time `<= 7.0s`.
- State file: `experiments/level3_ppo_loop/state.json`.
- Orchestrator: `scripts/level3_ppo_loop.py`.
- Default controller for level3 DR simulation: `ppo_level3_inference.py`.
- Default W&B project: `ADR-PPO-Racing-Level3`.
- Use `--from-scratch` only when intentionally creating a random-init baseline;
  otherwise continue from the best checkpoint in state, or the latest
  `level3_DR_initial` checkpoint if no best exists yet.
- Reward-only mode is no longer the default. The user has approved structural
  search for Level3, including observation layout, controller, reward
  structure, PPO/training structure, and hyperparameter changes.
- Hard boundary: do not edit Level3 track geometry/randomization to make the
  task easier, and do not accept any result unless it is hard-evaluated on
  `config/level3.toml`. The final target is the real Level3 track in
  `level3.toml`; `level3_dr.toml` is only a domain-randomized sim-to-real
  robustness/training config.
- Training curricula or alternate train configs may be explored only as named
  structural lanes. Final acceptance and state `best` must always come from
  hard eval on `config/level3.toml`.
- Each structural lane must have a clear hypothesis, source or local evidence,
  a unique proposal/run name, W&B logging, checkpoint milestone evaluation, and
  a post-run analysis packet before the next training chunk.
- Observation-layout experiments are open. The active deployed observation
  baseline is the remote-inspired local-obstacle v5 layout
  `level3_target_gate_nearest_gate_2obs_local_history_v5`; do not restore the
  rejected all-gates/v4 lane unless the user explicitly asks.
- The current structural roadmap is
  `experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md`.
  Its priority order is PPO correctness, clean longer-rollout baseline,
  observation/return normalization, asymmetric privileged critic, gate-phase
  reset curriculum, prioritized level replay, GRU, reward numbers, then speed.
- The immediate executable structural lane is
  `v31d_v31a_longer_rollout_maturation_15m`: it rejects the failed v31b/v31c
  normalization lanes, keeps v5 observations, loop052 reward/PPO numbers,
  corrected v30 semantics, hard eval on `config/level3.toml`, and the longer
  `256 envs x 128 steps` rollout geometry. It starts from the current best
  loop094/v31a 4M checkpoint, keeps observation/return normalization disabled,
  and evaluates 1/2/3/4/5/8/10/12/15M milestones before any next decision.
- The stateirving reference packet
  `experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md`
  is the current source-backed packet for v5 and remote reward-scale evidence.
- The orchestrator still retains historical structural hypotheses such as
  `v5_localobs_remote_reward`, but prefer the current framework/decision packet
  unless the user explicitly asks to revisit an older lane.
- Plateau guard is active by default. If consecutive evaluated trials do not
  improve success rate or mean gates, the loop should hold unless the user
  explicitly provides a new hypothesis or enables automatic hypothesis search.
- A state-level hold guard may be active after a post-run audit. If
  `state.json` records `stage2_after_loop014_escalation_audit` or another
  hold requiring user approval, `scripts/level3_ppo_loop.py` must hold before
  training unless the command explicitly passes `--override-state-hold` plus a
  named structural command and/or explicit parameter values with an
  `--approved-hypothesis-packet`.
- Use `--keep-latest-params` after analysis says the current hypothesis only
  needs more training evidence. It reuses the latest reward numbers and avoids
  an automatic reward proposal for that chunk.
- Use `--auto-hypothesis-search` to let the loop rotate through predefined
  reward-number hypotheses after plateau. Use `--relaxed-reward-bounds` only
  when wider reward-number search is intended.
- Use `--codex-autonomous-loop` for the user's unattended Codex-supervised
  mode. It records standing authorization for Codex to spawn analysis/research
  subagents and choose the next structural or reward hypothesis without per-run
  confirmation. It enables automatic structural search and does not bypass
  analysis, hard-eval, or long-run guards.
- Use the Level2 checkpoint step-curve packet
  `experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md`
  to calibrate Level3 training horizons: 30M is screening/debug evidence, while
  the first serious success-rate decision for a promising branch is 60M-90M.
  Promising means non-zero hard-eval success or meaningful gate progress.
- Use milestone-aware checkpoint evaluation for longer chunks. Evaluate
  intermediate 30M/60M/90M-style checkpoints plus recent checkpoints and never
  assume `final.ckpt` is best.
- Use `--allow-step-curve-maturation` only for a long continuation whose
  selected initial checkpoint already has promising hard-eval evidence recorded
  in `state.json`. It does not bypass the post-run analysis requirement.

## Steps

1. Read `experiments/level3_ppo_loop/state.json` if it exists.
2. Inspect the latest best checkpoint and recent trial summaries.
3. Run a dry run before changing the loop command:
   `pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run`.
4. For real work, run one bounded train/evaluate iteration:
   `pixi run -e gpu python scripts/level3_ppo_loop.py --max-iterations 1 --wandb-enabled`.
   In the user's unattended Codex-supervised loop, still use one script
   iteration at a time with `--codex-autonomous-loop`; do not use
   `--allow-unanalysed-multi-iteration`.
5. After every completed train/evaluate iteration, build a post-run analysis
   packet before choosing another training command:
   `pixi run -e gpu python scripts/analyze_level3_ppo_trial.py --wandb-entity aojili77-technical-university-of-munich --require-wandb-online`.
6. When the analysis is nontrivial, spawn exactly three separate subagents for
   evaluator metrics, W&B/PPO diagnostics, and structure/research synthesis
   using the generated briefs under
   `experiments/level3_ppo_loop/analysis/`.
7. The analyzer writes `pending_post_run_decision` into state. If its status is
   `awaiting_main_agent_decision`, do not launch the next train/evaluate chunk
   until the main agent has written a markdown decision packet under
   `experiments/level3_ppo_loop/decisions/`.
8. The main agent combines the analysis packet and subagent findings, then
   chooses exactly one of: `stop_target_met`, `hold_for_more_analysis`,
   `continue_same_hypothesis`, `change_reward_or_training_numbers`, or
   `launch_named_structural_lane`.
9. The next training command after analysis must attach both provenance files:
   `--analysis-packet <analysis.md>` and
   `--approved-hypothesis-packet <decision.md>`.
10. If the user wants automatic tuning after plateau, dry-run a bounded
   screening command with `--auto-structural-search` or
   `--auto-hypothesis-search`; prefer 20M-30M before any 80M extension.
11. If a 30M branch shows non-zero hard-eval success or meaningful gate progress,
   prefer continuing the same hypothesis toward 60M and then 90M with
   `--allow-step-curve-maturation`, rather than immediately changing reward
   numbers.
12. For nontrivial parameter changes, request or create a research synthesis in
    `experiments/level3_ppo_loop/research/` and attach it with
    `--research-packet`.
13. Stop when the hard gate is met. Report the checkpoint path and metrics.
14. Keep structural lanes explicit: proposal name, observation layout,
    controller/reward/training changes, source packet, and hard-eval summary
    must be recorded in state or a markdown packet.
15. Never modify `config/level3.toml` track geometry/randomization as a way
    to improve the metric. Any alternate training config, including
    `level3_dr.toml`, must be clearly labeled as training-only and still
    evaluated on `config/level3.toml`.

## Tuning Rules

- If success is low and mean gates is low, emphasize gate shaping and finish
  reward before optimizing speed.
- If multiple gate+safe trials plateau, do not keep scaling the same parameters.
  Move to a named structural hypothesis or hold for an evidence-backed review.
- `--relaxed-reward-bounds` may be used for exploratory screening, but only with
  evaluator gates and W&B conversion checks.
- For random-init experiments, use shorter checkpoint intervals so the loop can
  evaluate early candidates before committing to very long continuation.
- If crash rate or tilt is high, increase safety and smoothness penalties before
  pushing time.
- If success meets the target but time is too slow, increase time pressure and
  relax smoothness slightly.
- Treat PPO instability metrics as diagnostics only. Do not tune
  `learning_rate`, `ent_coef`, `target_kl`, `num_minibatches`,
  `update_epochs`, `hidden_dim`, or `n_obs` silently. They are allowed only as
  named structural/training-structure lanes with hard-eval follow-up.
- Do not treat W&B reward curves as the acceptance criterion. The evaluator CSV
  is the gate.
- Use W&B curves to diagnose why evaluator metrics moved: reward component
  balance, gate progress, finish/crash/timeout rates, tilt/smoothness pressure,
  KL/clip fraction, entropy, explained variance, and SPS.
- W&B analysis must happen after each completed iteration and before launching
  the next training iteration.
- Use W&B for live train curves and post-train evaluator metrics. If W&B auth is
  missing, ask the user to run `pixi run -e gpu wandb login` or set
  `WANDB_API_KEY`.
- After completing code, loop-state, analysis, decision, or loop-instruction
  changes, commit them and push to `aojili-test/main` by default. Before
  committing, inspect `git status` and avoid adding checkpoints, W&B run
  directories, CSV/NPZ datasets, logs, caches, or other bulky generated training
  artifacts unless the user explicitly asks.
- External evidence should influence the next experiment through a written
  synthesis packet. Do not let papers or GitHub examples override local metrics;
  use them to choose structural or reward hypotheses, then let hard eval on
  `config/level3.toml` decide.
- Do not edit notebooks unless the user asks. Keep loop changes in scripts,
  state, and small docs.

## Good Prompts

- "Use $level3-ppo-loop and run one dry-run."
- "Use $level3-ppo-loop, run one W&B-tracked 20M-step iteration, then summarize
  the best checkpoint and next tuning move."
- "Use $level3-ppo-loop to inspect state and propose the next parameter change
  without launching training."
- "Use $level3-ppo-loop to analyze the latest trial with W&B curves, ask
  subagents to review the analysis, then propose the next structural or reward move."
- "Use $level3-ppo-loop to dry-run a v5 local-obstacle observation experiment,
  but do not start training yet."
- "Use $level3-ppo-loop to dry-run `--structural-hypothesis
  v5_localobs_remote_reward`."
