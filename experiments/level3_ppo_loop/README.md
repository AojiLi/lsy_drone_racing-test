# Level3 PPO Loop

This folder stores the resumable train/evaluate/tune state for the Level3 PPO
controller.

## Target

- Final eval config: `config/level3.toml`
- Training configs may vary only as named structural lanes; do not modify the
  Level3 track geometry or randomization to make the task easier.
- Mean successful time: `<= 7.0s`
- Success rate: `>= 60%`
- W&B project: `ADR-PPO-Racing-Level3`

## Commands

Dry-run the next trial without training:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run
```

Run one bounded train/evaluate/tune iteration:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled
```

The orchestrator blocks `--max-iterations > 1` by default because post-run
analysis is required between iterations. Do not use
`--allow-unanalysed-multi-iteration` for the Codex-supervised loop; it is only
for an explicitly accepted blind run without analysis.

For the user's unattended Codex-supervised loop, run one train/evaluate chunk at
a time and let the Codex main agent do the analysis/subagent/research decision
between invocations. The latest completed chunk, loop112/v40, failed all hard
eval milestones with `0%` success and `0.0` mean gates, so do not relaunch the
old v40 training command. The immediate next step is the v41 diagnostic audit
described below.

Historical v40 command, retained only for provenance:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v40_sequence_memory_gru_phase_corridor_from_scratch \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_sequence_memory_gru_phase_corridor_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_launch_v40_sequence_memory_gru_phase_corridor.md
```

`--codex-autonomous-loop` records that Codex may spawn analysis and research
subagents and choose the next structural or reward hypothesis without per-run
user confirmation. It enables automatic structural/hypothesis search, but it
does not bypass W&B/evaluator analysis, decision packets, hard eval, or
long-run guards.

When the loop plateaus, it holds by default instead of repeatedly scaling the
same reward numbers. Prefer launching an explicit named structural lane with
attached analysis, research, and decision packets. For narrow reward-number
screens approved by a decision packet, use a bounded single-iteration command:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 20000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --auto-hypothesis-search
```

For a wider exploratory reward-number search, add `--relaxed-reward-bounds`.
Structural changes require a named `--structural-hypothesis` and provenance
packets; do not hide them inside reward-number search.

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 20000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --auto-hypothesis-search \
  --relaxed-reward-bounds
```

Long runs above `30M` steps require prior screened improvement unless you
explicitly pass `--allow-long-run-without-improvement`.

Start a new random-init baseline instead of continuing from the existing
`level3_DR_initial` checkpoint:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --from-scratch
```

If you launch the orchestrator from a different Python, keep train/eval
subprocesses on the GPU pixi environment:

```bash
<python> scripts/level3_ppo_loop.py \
  --python-command "pixi run -e gpu python" \
  --max-iterations 1 \
  --wandb-enabled
```

Before online W&B runs, log in once:

```bash
pixi run -e gpu wandb login
```

Each loop trial uses a stable W&B run id like `level3_loop_001_baseline`. The
training subprocess writes live PPO curves, and the loop resumes the same run
after evaluation to log `eval/success_rate`, `eval/mean_time_s_success`,
`eval/crash_rate`, `eval/score`, and a summary table.

Run a shorter smoke-sized iteration:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 65536 \
  --checkpoint-interval 32768 \
  --num-envs 8 \
  --num-steps 16 \
  --jax-device cpu \
  --no-cuda \
  --eval-seeds 2
```

The loop writes local logs, summaries, and the resumable `state.json` here.
The hard stop condition is based on evaluator metrics, not PPO training reward.

## Post-Run Analysis

After each completed train/evaluate iteration, build an analysis packet before
starting the next training run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

The analyzer combines:

- evaluator CSV metrics from the loop state
- sampled W&B curves for `train/*`, `losses/*`, `race/*`, and
  `reward_components/*`
- evaluator diagnosis and a candidate next command
- subagent briefs for evaluator review, W&B curve review, and structure/research
  synthesis

Outputs are written under `experiments/level3_ppo_loop/analysis/` and the paths
are copied back into the selected trial in `state.json`.

For Codex-driven analysis, the main agent should hand those generated briefs to
parallel subagents, compare their findings, and then choose one of:

- stop because the hard gate is met
- hold for more analysis
- continue the same hypothesis
- change reward or training numbers as an explicit named lane
- launch a named structural lane

For Codex-driven autonomy, the main agent should attach ordinary analysis with
`--analysis-packet`, source-backed research with `--research-packet`, and a
main-agent decision packet with `--approved-hypothesis-packet`. Analysis packets
never bypass plateau guards by themselves.

## Structural Boundary

Structural search is now active. Observation layout, controller architecture,
reward structure, PPO/training structure, and training distribution may change
only as explicit named lanes with a research packet, a decision packet, W&B
logging, milestone hard eval, and post-run analysis.

Current immediate lane:

```text
v42_gru_v10_gate_phase_reset_curriculum_from_scratch
```

v41 passed the GRU/v10 wiring audit, so the next bounded train/evaluate lane is
v42: keep GRU/v10 and v39 gate-acquisition rewards, start from scratch, add the
training-only v33-style gate-phase reset curriculum, and hard-eval only on
unchanged `config/level3.toml`. The goal of v42 is first-gate acquisition and
nonzero normal-start hard-eval gate progress, not speed optimization.

## Research-Guided Tuning

For tuning decisions that need papers, GitHub examples, or PPO references, use
the templates in `experiments/level3_ppo_loop/research/`. Research may guide
either reward-number changes or named structural hypotheses, but local hard eval
on `config/level3.toml` decides acceptance.

Attach the main-agent synthesis to the next trial:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --research-packet experiments/level3_ppo_loop/research/<synthesis>.md
```

Attached packets are copied into each trial record in `state.json`, so the
reason for a parameter move is traceable later.
