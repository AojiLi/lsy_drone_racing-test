# Codex Goal: Autonomous Level3 PPO Loop

Use this as the `/goal` instruction for an unattended Codex-supervised run.

```text
Use the level3-ppo-loop skill.

Objective: train and tune the Level3 PPO controller until hard evaluation on
config/level3_dr.toml reaches success_rate >= 0.60 and mean successful race
time <= 7.0s. Do not modify the Level3 track geometry or randomization.

Work loop:

1. Read AGENTS.md, .agents/skills/level3-ppo-loop/SKILL.md, and
   experiments/level3_ppo_loop/state.json.
2. If state.best already meets the target, stop and report checkpoint path,
   success rate, mean successful time, crash rate, and W&B link.
3. Choose exactly one bounded next training chunk. Use
   scripts/level3_ppo_loop.py, never ad hoc training commands. Use
   --max-iterations 1 only.
4. Before a real run, run the same command with --dry-run and inspect the JSON.
5. Run the chosen one-iteration train/evaluate chunk through the GPU pixi env
   with W&B enabled:
   pixi run -e gpu python scripts/level3_ppo_loop.py --max-iterations 1
   --wandb-enabled --wandb-entity aojili77-technical-university-of-munich
6. After training/evaluation completes, immediately run:
   pixi run -e gpu python scripts/analyze_level3_ppo_trial.py
   --wandb-entity aojili77-technical-university-of-munich
   --require-wandb-online
7. Spawn exactly three separate reviews using the generated briefs for:
   evaluator_metrics, wandb_ppo_diagnostics, and structure_research_synthesis.
   If actual subagent tools are unavailable, perform the three reviews as
   separate written sections.
8. The main agent must synthesize those reviews into a markdown decision packet
   under experiments/level3_ppo_loop/decisions/. Use the decision packet
   template. Choose exactly one next action:
   stop_target_met, hold_for_more_analysis, continue_same_hypothesis,
   change_reward_or_training_numbers, or launch_named_structural_lane.
9. Do not start another training chunk while
   state.pending_post_run_decision.status is awaiting_main_agent_decision.
10. For the next training command after analysis, attach both:
   --analysis-packet <latest analysis md/json>
   --approved-hypothesis-packet <main-agent decision md>
11. If a 30M structural/reward branch has non-zero success or meaningful gate
   progress, prefer maturing the same hypothesis toward 60M-90M before
   discarding it. Use milestone-aware checkpoint evaluation.
12. If changing framework/structure, keep it as a named structural lane with
   explicit evidence. Allowed areas are observation, controller, reward
   structure, PPO/training structure, and hyperparameters. The Level3 track
   itself is immutable.
13. Keep W&B online logging in project ADR-PPO-Racing-Level3.
14. Repeat until target is met, a hard blocker appears, or the machine/resource
   budget is exhausted. Final report must include best checkpoint, success
   rate, mean successful time, crash rate, mean gates, W&B link, what changed,
   and the next recommended action.

Recommended first structural screen if no v5 trial exists:

pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_localobs_remote_reward
```
