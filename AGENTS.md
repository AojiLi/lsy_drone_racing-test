# AGENTS.md

## Level3 PPO Loop

- Primary objective: train a PPO controller for final evaluation on
  `config/level3.toml` with
  mean successful race time `<= 7.0s` and success rate `>= 0.60`.
- Treat `experiments/level3_ppo_loop/state.json` as the resumable experiment
  state. Read it before launching new training and update it after each
  train/evaluate chunk.
- Use `scripts/level3_ppo_loop.py` for the train/evaluate/tune loop instead of
  hand-running ad hoc commands. Start with `--dry-run` when changing the loop.
- Use the hard gate from competition-style checkpoint evaluation, not training
  reward alone. Training reward can guide debugging, but it is not the target.
- Use the Level2 checkpoint step-curve packet
  `experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md`
  to calibrate training horizons: treat 30M as screening/debug evidence, not a
  final success-rate judgment. If a branch has non-zero hard-eval success or
  meaningful gate progress, mature the same hypothesis toward 60M-90M before
  rejecting it.
- Use milestone-aware checkpoint evaluation for longer chunks. Prefer checking
  intermediate 30M/60M/90M-style checkpoints plus recent checkpoints; do not
  assume the final checkpoint is best.
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
  The latest pasted-framework synthesis is
  `experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md`.
  Its priority order is PPO correctness, clean longer-rollout baseline,
  observation/return normalization, asymmetric privileged critic, gate-phase
  reset curriculum, prioritized level replay, GRU, reward numbers, then speed.
- v32 asymmetric privileged-Critic support and zero-update Actor parity have
  passed. The first v32 training screen, `loop099`, reached 19% success /
  1.66 mean gates / 81% crash at its 3M checkpoint on `config/level3.toml`,
  close to but not better than the loop097 global best of 20% / 1.66 / 80%.
- loop100 matured v32 from loop099 3M to about 18M and still did not beat
  loop097: best loop100 was 19% success / 1.65 mean gates / 81% crash on
  unchanged `config/level3.toml`. Do not continue v32 privileged-Critic
  maturation without a new explicit decision packet.
- loop101 tested v33 gate-phase reset curriculum for 10M and tied, but did not
  beat, the old frontier: best loop101 was 20% success / 1.69 mean gates /
  80% crash with 6.873s mean successful time. The 8M checkpoint reached 1.81
  mean gates but only 19% success. Do not continue v33 as-is without a new
  explicit decision packet.
- loop102 tested v34 offline train-pool PLR for 10M and regressed: best loop102
  was only 17% success / 1.59 mean gates / 83% crash, and final fell to 10%
  success / 1.43 mean gates / 90% crash. Do not continue v34 as-is and do not
  start future training from loop102 checkpoints.
- loop106 tested v36 online competence-gated level replay for 10M and did not
  beat the loop101 frontier. Its best checkpoint was 1M with 20% success /
  1.63 mean gates / 80% crash / 7.744s, and final collapsed to 14% success /
  1.41 mean gates / 86% crash. Do not continue v36, tune replay probability,
  or start future training from loop106 checkpoints.
- loop107 tested `v37_gru_transfer_memory_structure_from_loop101` for 5M. Its
  best checkpoint was the 1M checkpoint with 21% success / 1.66 mean gates /
  79% crash / 7.578s; later checkpoints drifted down to 15%, 12%, 12%, and
  17% success. Do not continue v37 from loop107 final.
- loop112 tested
  `v40_sequence_memory_gru_phase_corridor_from_scratch` and regressed hard:
  every 1M/2M/3M/4M/final milestone had `0%` success and `0.0` mean gates, with
  all failures at gate 0. Do not continue v40 as-is, do not mature it to a long
  run, and do not start future training from loop112 checkpoints.
- v41 audited GRU/v10 wiring after loop112 and passed: recurrent Actor
  zero-update parity, train/eval action-scale parity, hidden-state reset/carry
  parity, v10 observation parity/sanity, and recurrent PPO gradient/update
  sanity were all clean. This rules out an obvious wiring bug as the cause of
  v40's zero-gate failure.
- The immediate next train/evaluate lane is
  `v42_gru_v10_gate_phase_reset_curriculum_from_scratch`, approved by
  `experiments/level3_ppo_loop/decisions/2026-06-23_v41_clean_launch_v42_gru_v10_gate_phase_curriculum.md`
  and sourced by
  `experiments/level3_ppo_loop/research/2026-06-23_level3_v42_gru_v10_gate_phase_curriculum_plan.md`.
  It keeps GRU/v10 and v39 gate-acquisition rewards, starts from scratch, adds
  the training-only v33-style gate-phase reset curriculum, and hard-evals only
  on unchanged `config/level3.toml`.
- loop103 tested v35 competence-gated gate-phase reset for 10M and did not
  beat the loop101 frontier: best loop103 was 19% success / 1.68 mean gates /
  81% crash with 7.245s mean successful time, and final fell to 17% success /
  1.58 mean gates / 83% crash. Do not continue v35 as-is and do not start
  future training from loop103 checkpoints.
- For full training, run through the GPU pixi environment:
  `pixi run -e gpu python scripts/level3_ppo_loop.py --max-iterations 1 --wandb-enabled`.
- For the user's unattended Codex-supervised loop, use
  `--codex-autonomous-loop` so each run records that Codex may spawn analysis
  and research subagents and choose the next structural or reward hypothesis
  without per-run confirmation.
- For a long continuation justified by the Level2 step curve, use
  `--allow-step-curve-maturation` only when the selected initial checkpoint has
  promising hard-eval evidence already recorded in `state.json`. This does not
  bypass the requirement to analyze after the chunk.
- If `state.json` records a post-audit hold such as
  `stage2_after_loop014_escalation_audit`, the loop must not start training
  unless the command explicitly uses `--override-state-hold` together with a
  named structural command and/or explicit parameter values plus an
  `--approved-hypothesis-packet`.
- Keep deployment strictly
  observation/history -> PPO actor -> roll/pitch/yaw/thrust; do not add MPC,
  waypoint planners, subgoal policies, rule controllers, static seed replay, or
  inference-time safety shields unless a later explicit structural packet
  approves them.
- For live W&B tracking, log in first with `pixi run -e gpu wandb login` or set
  `WANDB_API_KEY` in the shell before starting the loop.
- Default W&B project for Level3 loop runs is `ADR-PPO-Racing-Level3`.
- Do not overwrite `notebooks/train_level3_ppo.ipynb` unless explicitly asked;
  it is an interactive planning/debug notebook and may contain local edits.
- Checkpoints live under `lsy_drone_racing/control/checkpoints/`. Prefer
  continuing from the best level3 checkpoint recorded in state; otherwise use
  the latest `level3_DR_initial` checkpoint when compatible.
- Use `--from-scratch` when intentionally starting a new random-init baseline.
  After that, let later runs continue from the best checkpoint recorded in
  `state.json`.
- Generated loop logs and CSVs belong under `experiments/level3_ppo_loop/`.
  Keep final summaries concise and include the best checkpoint path, success
  rate, mean successful time, crash rate, and next action.
- After completing code, loop-state, analysis, decision, or loop-instruction
  changes for this project, commit them and push to `aojili-test/main` by
  default. Before committing, always inspect `git status` and avoid adding
  checkpoints, W&B runs, CSV/NPZ datasets, logs, caches, or other bulky
  generated training artifacts unless the user explicitly asks.
- After each completed train/evaluate iteration, run
  `scripts/analyze_level3_ppo_trial.py` before launching another training
  iteration. The analysis packet must combine evaluator CSV metrics, W&B curves,
  W&B reward components, PPO diagnostics, and a next-lane recommendation.
- The analyzer creates a post-run decision gate in `state.json`. If
  `pending_post_run_decision.status` is `awaiting_main_agent_decision`, do not
  launch another train/evaluate chunk until the main agent has synthesized the
  reviews into a markdown decision packet under
  `experiments/level3_ppo_loop/decisions/`.
- Do not run `scripts/level3_ppo_loop.py` with `--max-iterations > 1` for the
  Codex-supervised loop. Unattended mode still means one train/evaluate chunk,
  then analyzer, subagent review, research if needed, and a main-agent decision
  before the next chunk.
- For substantive post-run analysis, use exactly three separate subagents:
  evaluator metrics, W&B/PPO diagnostics, and structure/research synthesis. The
  main agent owns the final decision and must enforce the immutable
  `level3.toml` hard eval.
- The main-agent decision packet must choose exactly one next action:
  `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`,
  `change_reward_or_training_numbers`, or `launch_named_structural_lane`.
- The next training command after a completed analysis must attach both the
  analysis packet and the main-agent decision packet, using `--analysis-packet`
  and `--approved-hypothesis-packet`. Structural lanes must be named explicitly
  and may not modify the Level3 race track.
- For nontrivial tuning changes, use research-guided tuning: spawn distinct
  research agents for papers, GitHub/open-source examples, and reward tuning
  references; synthesize their source-backed findings into a markdown packet
  under `experiments/level3_ppo_loop/research/`; attach it to the next run with
  `--research-packet`. External evidence may guide structural hypotheses, but
  local hard eval on `config/level3.toml` decides.
