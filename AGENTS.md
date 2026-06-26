# AGENTS.md

## Purpose

- This file is durable repository guidance for Codex. Keep it concise and
  practical: record rules that should apply every time an agent works in this
  repo.
- Do not use this file as a full experiment log. Run-specific metrics belong in
  `experiments/level3_ppo_loop/state.json`, analysis packets, and decision
  packets. Add only durable conclusions, hard boundaries, current blockers, and
  workflow rules here.
- For detailed Level3 PPO workflow, use the repo skill
  `.agents/skills/level3-ppo-loop/SKILL.md`.
- For Level3 MPPI oracle/controller/teacher-data workflow, use the repo skill
  `.agents/skills/level3-mppi-loop/SKILL.md`.
- For v54/v55 low-level reference-tracker qualification, use the repo skill
  `.agents/skills/level3-tracker-loop/SKILL.md`.
- For v56 deterministic gate-front planner tuning, use the repo skill
  `.agents/skills/level3-geometric-planner-loop/SKILL.md`.

## Level3 PPO Objective

- Primary objective: train a PPO controller for final evaluation on
  `config/level3.toml` with success rate `>= 0.60` and mean successful race
  time `<= 7.0s`.
- Use the hard gate from competition-style checkpoint evaluation. Training
  reward and W&B curves are diagnostics, not acceptance criteria.
- Final acceptance and `state.json` `best` must always come from hard eval on
  unchanged `config/level3.toml`.
- Current completion-first controller objective: the user has approved a
  non-pure-PPO Level3 controller lane whose first priority is finishing
  unchanged `config/level3.toml`. For that lane, success rate is the primary
  screen, and a slower `15s-20s` successful time is acceptable as an
  intermediate milestone if the built-in 30s environment timeout permits it.
  Speed optimization comes after reliable completion. The preferred next
  architecture is v54: an upper planner/geometric module generates a short
  local reference trajectory, and a native reference-tracking PPO low-level
  controller follows that trajectory. The v53 attempt to wrap the stable
  Level2 PPO checkpoint through a virtual local-gate adapter was action-finite
  but failed first-gate progress on seeds `101-105`, so it is no longer the
  primary route.
- Current tracker-first objective: the bottom PPO tracker's first required
  ability is accurate, smooth reference following, not direct Level3 gate
  completion. Train and qualify hover, point, line, L-shape, curve, braking,
  heading, and multi-point reference tracking before treating planner+tracker
  Level3 gate pass as the primary exam.
- Current v58 tracker correction: do not launch the existing semantic
  planner-reference training as the next step. The user rejected any tracker
  route that smells like teaching the bottom PPO to pass gates. The bottom
  tracker must learn generic trajectory-command following, not gate semantics.
  Future inputs should prioritize current/next/lookahead points, desired
  velocity/speed, desired heading, and generic hold/low-speed command intent.
  Waypoint labels are optional diagnostics, not the main interface.
- Current v60 tracker proposal: replace v58 with a
  `reference_command_tracker_no_gate_reward` lane. The reward must be local:
  reference tracking, speed/velocity tracking, heading tracking, braking/hold
  behavior, action smoothness, and small safety penalties only. Do not add
  gate-pass, finish, aperture-crossing, race-progress, or stage-progress
  rewards to the bottom tracker. Use clean observation layout
  `level3_reference_tracker_command_v3`: self state, reference horizon, desired
  velocity/speed/heading, generic command masks, last action, and short history
  only. Do not include gate, obstacle, or planner phase inputs in this clean
  bottom-tracker baseline.
- Current v59 tracker proposal: after v60 no-gate command tracking is proven, allow a
  small local safety reflex in the tracker. The tracker still follows planner
  references as its main job; safety features such as nearest obstacle relative
  position/distance, and possibly minimal gate-frame clearance, are auxiliary
  collision-margin inputs. Do not add gate-pass, finish, race-progress, or
  stage-progress rewards to this tracker lane, and do not make the bottom PPO
  learn an autonomous gate-passing strategy.

## Hard Boundaries

- Never edit Level3 track geometry or randomization to make the task easier.
  `config/level3.toml` is the immutable target. `config/level3_dr.toml` is only
  a domain-randomized training/robustness config.
- Keep PPO-lane deployment strictly
  observation/history -> PPO actor -> roll/pitch/yaw/thrust. v51 explicitly
  allowed a deterministic planner-guidance module as deployed observation
  computation only. v52 explicitly approves a separate MPPI oracle/teacher loop
  that may output actions during MPPI evaluation and teacher-data generation.
  The 2026-06-25 completion-first approval explicitly allows a separate
  non-PPO hybrid/controller lane to output actions directly, including
  planner/state-machine/MPPI actions, as long as it remains separate from PPO
  training results and is hard-evaluated on unchanged `config/level3.toml`.
  Do not mix MPPI/planner action output into PPO lanes, add static seed replay,
  or weaken the target track.
- Training curricula and alternate train configs are allowed only as named
  structural lanes. They must still be hard-evaluated on `config/level3.toml`.
- Do not overwrite `notebooks/train_level3_ppo.ipynb` unless the user explicitly
  asks; it is an interactive planning/debug notebook and may contain local edits.

## Source Of Truth

- Treat `experiments/level3_ppo_loop/state.json` as the resumable experiment
  state. Read it before launching training and update it after each
  train/evaluate chunk.
- Before training, inspect the latest analysis packet and main-agent decision
  packet referenced by `state.json`.
- If `state.json` has
  `pending_post_run_decision.status == "awaiting_main_agent_decision"`, do not
  launch another train/evaluate chunk until the main agent has written a
  markdown decision packet under `experiments/level3_ppo_loop/decisions/`.
- Checkpoints live under `lsy_drone_racing/control/checkpoints/`. Prefer
  continuing from the best Level3 checkpoint recorded in state; otherwise use
  the latest compatible `level3_DR_initial` checkpoint. Use `--from-scratch`
  only when intentionally starting a random-init baseline.
- Generated loop logs, CSVs, analysis packets, decision packets, and research
  packets belong under `experiments/level3_ppo_loop/`.

## Required PPO Loop Workflow

- Use `scripts/level3_ppo_loop.py` for PPO train/evaluate/tune work instead of
  hand-running ad hoc commands. For MPPI oracle/controller evaluation, use
  `.agents/skills/level3-mppi-loop/SKILL.md` and the MPPI evaluator workflow.
- Start with a dry run when changing the loop command:

  ```bash
  pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run
  ```

- For full training, run through the GPU pixi environment and only one bounded
  train/evaluate iteration at a time:

  ```bash
  pixi run -e gpu python scripts/level3_ppo_loop.py --max-iterations 1 --wandb-enabled
  ```

- For the user's unattended Codex-supervised loop, add
  `--codex-autonomous-loop`. This authorizes Codex to spawn analysis/research
  subagents and choose the next structural or reward hypothesis without
  per-run confirmation, but it does not bypass hard eval, analysis, or decision
  gates.
- Do not run `scripts/level3_ppo_loop.py` with `--max-iterations > 1` for the
  Codex-supervised loop.
- For live W&B tracking, log in first with
  `pixi run -e gpu wandb login` or set `WANDB_API_KEY`. Default W&B project:
  `ADR-PPO-Racing-Level3`.
- After every completed train/evaluate iteration, run the analyzer before
  launching another training iteration:

  ```bash
  pixi run -e gpu python scripts/analyze_level3_ppo_trial.py --wandb-entity aojili77-technical-university-of-munich --require-wandb-online
  ```

- For substantive post-run analysis, use exactly three separate subagents:
  evaluator metrics, W&B/PPO diagnostics, and structure/research synthesis. The
  main agent owns the final decision and must enforce the immutable
  `config/level3.toml` hard eval.
- The main-agent decision packet must choose exactly one next action:
  `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`,
  `change_reward_or_training_numbers`, or `launch_named_structural_lane`.
- After the analyzer, three required reviews, and main-agent decision packet are
  complete, spawn one additional reader-note subagent to explain the completed
  loop in plain Chinese for the user. This reader-note subagent is not a
  decision reviewer and must not replace the three required reviews. Write the
  final human-readable note under `drone_notes/level3_loops/`, using
  `scripts/write_level3_loop_reader_note.py` as the metric/path scaffold when
  useful.
- The next training command after a completed analysis must attach both the
  analysis packet and the main-agent decision packet, using `--analysis-packet`
  and `--approved-hypothesis-packet`. Structural lanes must be named explicitly
  and may not modify the Level3 race track.
- For any structural lane that changes code or config semantics before
  training, split implementation and verification into a builder/checker gate.
  A builder agent may edit the code and run local checks, but it may not approve
  its own work. A checker agent must be read-only, rediscover the relevant
  checks from repo configuration and loop context, run/inspect them, and report
  `ALL GREEN` or `FAILED` with concrete `file:line` evidence. The main agent
  decides whether to launch training only after checker approval.
- The builder/checker gate is required for changes touching observation layout,
  planner-guidance features, inference action path, PPO/training semantics,
  reward structure, evaluator/parity scripts, or loop orchestration. It is not
  required for pure analysis, decision, or reader-note markdown updates.
- If checker fails, route the failure back to builder for the smallest root
  cause fix, then run checker again. Do not weaken tests, skip checks, or
  silently change `config/level3.toml`.

## Tuning And Research Rules

- Reward-only mode is no longer the default. The user has approved structural
  search for Level3, including observation layout, controller, reward
  structure, PPO/training structure, and hyperparameter changes.
- Each structural lane must have a clear hypothesis, source or local evidence,
  a unique proposal/run name, W&B logging, checkpoint milestone evaluation, and
  a post-run analysis packet before the next training chunk.
- Nontrivial tuning changes should be research-guided. Spawn distinct research
  agents for papers, GitHub/open-source examples, and reward tuning references;
  synthesize their findings into a markdown packet under
  `experiments/level3_ppo_loop/research/`; attach it with `--research-packet`.
  External evidence may guide hypotheses, but local hard eval decides.
- Use the Level2 checkpoint step-curve packet
  `experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md`
  to calibrate horizons: treat 30M as screening/debug evidence, not a final
  success-rate judgment.
- If a branch has non-zero hard-eval success or meaningful gate progress, prefer
  maturing the same hypothesis toward 60M-90M before rejecting it.
- Use milestone-aware checkpoint evaluation for longer chunks. Evaluate
  intermediate 30M/60M/90M-style checkpoints plus recent checkpoints; never
  assume the final checkpoint is best.
- Use `--allow-step-curve-maturation` only when the selected initial checkpoint
  already has promising hard-eval evidence recorded in `state.json`. It does
  not bypass post-run analysis.
- If `state.json` records a state-level hold such as
  `stage2_after_loop014_escalation_audit`, do not start training unless the
  command explicitly uses `--override-state-hold` together with a named
  structural command and/or explicit parameter values plus an
  `--approved-hypothesis-packet`.

## Observation And Roadmap

- Observation-layout experiments are open. The active deployed observation
  baseline is the remote-inspired local-obstacle v5 layout
  `level3_target_gate_nearest_gate_2obs_local_history_v5`. Do not restore the
  rejected all-gates/v4 lane unless the user explicitly asks.
- Current structural roadmap:
  `experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md`.
- Latest pasted-framework synthesis:
  `experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md`.
- Current MPPI oracle/teacher plan:
  `experiments/level3_ppo_loop/research/2026-06-25_level3_v52_mppi_oracle_teacher_plan.md`.
- Current completion-first hybrid controller plan:
  `experiments/level3_ppo_loop/research/2026-06-25_level3_v53_completion_first_hybrid_controller_plan.md`.
- Current reference-tracker PPO plan:
  `experiments/level3_ppo_loop/research/2026-06-25_level3_v54_reference_tracker_ppo_plan.md`.
- Roadmap priority order: PPO correctness, clean longer-rollout baseline,
  observation/return normalization, asymmetric privileged critic,
  gate-phase reset curriculum, prioritized level replay, GRU, reward numbers,
  then speed.

## Current Frontier And Gate

- `state.json` is the source of truth if this summary drifts.
- Current global best recorded in state is
  `level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight:1M`:
  `21%` success, `1.66` mean gates, `79%` crash, and `7.578s` mean successful
  time. Target is not met.
- loop122 tested `v51_planner_guidance_obs_ppo256_from_loop110_3m` for 30M.
  Its best hard-eval checkpoint was 10M with `18%` success, `1.42` mean gates,
  `81%` crash, and `6.991s` mean successful time. It did not meet target or
  beat the current global best.
- The loop122 post-run gate was resolved by:
  `experiments/level3_ppo_loop/decisions/2026-06-25_loop122_hold_for_v51_planner_diagnostics.md`.
- v53 completion-first hybrid controller smoke implemented planner reference
  -> virtual Level2 gate adapter -> Level2 PPO tracker. It was action-finite
  but scored `0%` success and `0.00` mean gates on seeds `101-105`; do not
  promote it to dev `1-20` or continue virtual-gate adapter tuning as the
  primary route without a new explicit decision.
- The immediate next controller/training-support lane is
  `v54_reference_trajectory_tracker_ppo`, approved by:
  `experiments/level3_ppo_loop/decisions/2026-06-25_launch_v54_reference_tracker_ppo.md`.
  This lane trains a native PPO low-level tracker for hover, point tracking,
  local trajectory tracking, heading alignment, gate-aperture centering, and
  obstacle-aware low-speed control. The upper planner owns route choice,
  nominal far-field guidance, slowdown near `0.7m-1.0m`, visible-geometry
  replanning, and reference trajectory generation. Do not launch long training
  until builder/checker support and hover/point/gate-aperture smoke checks pass.
- The current tracker-specific next lane is
  `v55_tracker_qualification_curriculum`: prove the low-level PPO can follow
  reference points and short trajectories before planner-driven Level3 long
  training. Use `.agents/skills/level3-tracker-loop/SKILL.md`. Do not approve a
  manual long-training command until tracker qualification and strict
  planner-integration smoke pass.
- v55 gate-aperture reward shaping is no longer a required tracker stage.
  Because the upper planner owns pre-gate/aperture/post-gate reference
  generation, the bottom PPO tracker only needs to prove free-space trajectory
  following. After `zigzag_or_lemniscate_tracking`, go directly to
  `planner_integration_smoke` on unchanged `config/level3.toml`; use
  `gate_aperture_reference` only as an optional diagnostic if planner-generated
  references appear untrackable.
- The first planner-smoke implementation is `GeometricSlowGatePlanner` inside
  `lsy_drone_racing/control/level3_reference_tracker.py`: deterministic
  gate-frame state machine, five phases, near-gate slowdown, hysteretic phase
  switching, pre/aperture/post/recovery references, and simple visible-obstacle
  waypoint offsets. It must output references only; the PPO tracker remains the
  only action source.
- Formal planner smoke with `GeometricSlowGatePlanner` and the zigzag-qualified
  tracker checkpoint passed on seeds `101-120`: `20/20` first-gate progress,
  `1` gate0 pass on seed `113`, `2/20` early terminations, finite actions, and
  unchanged `config/level3.toml`. The next unlocked stage is
  `manual_long_level3_training_review`; do not launch long training without that
  review packet.
- A longer 500-step trace diagnostic with the same planner/checkpoint/seeds
  produced `20/20` first-gate progress and `3/20` gate0 passes, but `15/20`
  episodes still ended by contact. Successful gate0 passes had near-plane Y/Z
  error around `0.10m-0.19m`; failed plane-crossing seeds were commonly
  `0.5m+` off aperture. Long training remains held. The next move is a
  planner-only `GeometricSlowGatePlanner` tuning pass: align longer, cross
  slower, handle near-plane/off-aperture states by backing out to pre-gate, and
  prevent recover before a real target-gate switch.
- The immediate next loop is `v56_geometric_gate_crossing_tuning_loop`, defined
  by `.agents/skills/level3-geometric-planner-loop/SKILL.md`. Keep the
  zigzag-qualified PPO tracker checkpoint fixed, run unchanged `config/level3.toml`
  on seeds `101-120` for 500 steps with trace output, and iterate only on
  deterministic gate-front planner policy until the smoke target reaches
  `gate0_pass_count >= 10/20`, contact terminations `<= 8/20`, and first-gate
  progress `20/20`. Do not start PPO training or long Level3 training during
  this loop. Only an environment `target_gate` transition counts as a real gate
  pass for planner control flow; custom pass-checker logic is diagnostic only.
  Change only one planner strategy knob per v56 iteration. The legacy
  `planner_integration_smoke` gate checker is only a compatibility/plumbing
  check for v56; do not treat its `passed=true` result as v56 success unless
  the stronger v56 target also passes.
- v57a fixed the phase3 -> phase4 planner reference discontinuity. The jump
  fell from about `0.740m` to `0.280m`, reference error from `0.783m` to
  `0.340m`, and action delta from `0.727` to `0.491`, while `gate0 pass`
  stayed `2/20`, contact stayed `20/20`, and near-plane phase4 speed remained
  too high. The earlier v58 semantic-reference route is now held because it
  risks adding gate-like semantics/rewards to the bottom tracker. The next
  proposed lane is `v60_reference_command_tracker_no_gate_reward`: teach the
  tracker to follow generic trajectory commands with hold/low-speed behavior
  but no gate/aperture/race reward.
- v59 remains a future extension, not the immediate training command:
  `v59_reference_tracker_with_local_safety_reflex` keeps reference tracking
  dominant and adds only weak local obstacle/frame safety penalties or inputs
  after the generic no-gate-reward command tracker is proven.
- loop122 analysis packet:
  `experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_analysis.md`.

## Rejected Or Held Lanes

- v31d clean longer-rollout maturation did not beat the loop097/loop101
  frontier. Do not continue v31d without a new explicit decision packet.
- v32 asymmetric privileged-Critic support and zero-update Actor parity passed,
  but loop099/loop100 did not beat the frontier. Do not continue v32 maturation
  without a new explicit decision packet.
- v33 gate-phase reset curriculum tied but did not beat the frontier. v35
  competence-gated gate-phase reset also did not beat the frontier. Do not
  continue either as-is.
- v34 offline train-pool PLR regressed. v36 online competence-gated level replay
  did not beat the frontier and collapsed by final. Do not continue these lanes,
  tune replay probability, or start future work from their checkpoints.
- v37 GRU transfer produced the current global best at the 1M checkpoint, but
  later checkpoints drifted down. Do not continue from loop107 final.
- v40-v44 recurrent/GRU/BC/sequence-retention lanes failed to acquire or
  preserve hard-eval gate progress. v41 audited GRU/v10 wiring and found no
  obvious wiring bug. Do not continue v40-v44 as-is or start future work from
  their checkpoints.
- v45 and v47 retention lanes proved retention mechanisms were active but did
  not beat the frontier. Do not continue them as-is or start from their finals.
- v48 contact-conversion reward structure regressed. Do not mature it or start
  future work from loop118 checkpoints.
- v49 hidden512 long-horizon recovery did not convert PPO training signals into
  gate/finish progress; W&B showed near-zero update pressure symptoms. Do not
  continue v49 toward 90M/120M or start from loop120 final.
- v50 hidden512 update-pressure follow-up improved update diagnostics but did
  not meet the target or beat the global best. It has been rejected as the next
  immediate move by the loop121 v51 decision packet.
- v51 planner-guidance observation did not beat the frontier and must not be
  continued as-is. Further planner-as-observation work requires diagnostics;
  the current next route is the separate v52 MPPI oracle/teacher loop.
- v52 local MPPI tuning did not produce nonzero success and should not be
  continued as a weight-tuning exercise. The next route is a completion-first
  controller redesign, not more local MPPI coefficient sweeps.

## Git And Generated Files

- After completing code, loop-state, analysis, decision, or loop-instruction
  changes, inspect `git status`, commit the intended files, and push to
  `aojili-test/main` by default.
- Do not add checkpoints, W&B run directories, CSV/NPZ datasets, logs, caches,
  or other bulky generated training artifacts unless the user explicitly asks.
- Do commit small markdown reader notes under `drone_notes/level3_loops/`.
  Keep Obsidian workspace/config files under `drone_notes/.obsidian/` ignored.
- If unrelated user or generated changes are present, do not revert them and do
  not include them in commits unless they are part of the requested work.

## Final Summaries

- Keep final summaries concise.
- Include the best checkpoint path, success rate, mean successful time, crash
  rate, target-met status, and next action.
- Mention any tests, dry-runs, analyzer runs, W&B checks, or hard-eval steps
  that were not run.
