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
between invocations. The current loop is repeated structural search, not a
one-off structure change: after each bounded chunk, Codex must analyze the
result, collect exactly three reviews, write a decision packet, and either hold
or launch the next named structural lane.

The latest completed chunk, loop121/v50, fixed the hidden512 PPO update-pressure
symptom but did not beat the frontier: best checkpoint 25M had `18%` success,
`1.56` mean gates, `80%` crash, `2%` timeout, and `6.283s` mean successful
time. Do not continue v50 as the immediate next move. The approved next lane is
one bounded v51 planner-guidance observation PPO256 screen, hard-evaluated on
unchanged `config/level3.toml`.

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

## Builder/Checker Gate

For structural lanes that require code changes, use a two-agent gate before
training:

- builder implements the approved change and runs local checks;
- checker is read-only, reruns/discovers the relevant checks, and reports
  `ALL GREEN` or `FAILED` with concrete file/line evidence;
- the main agent decides whether the evidence is strong enough to launch the
  next bounded train/evaluate chunk.

This gate is required for observation, planner-guidance, inference action path,
PPO/training semantics, reward structure, evaluator/parity script, and loop
orchestration changes. It is not required for pure markdown analysis, decisions,
or reader notes. The checker should always confirm that `config/level3.toml`
track geometry/randomization was not changed.

## Structural Boundary

Structural search is now active. Observation layout, controller architecture,
reward structure, PPO/training structure, and training distribution may change
only as explicit named lanes with a research packet, a decision packet, W&B
logging, milestone hard eval, and post-run analysis.

Current immediate lane:

```text
v51_planner_guidance_obs_ppo256_from_loop110_3m
```

v50 showed that stronger hidden512 PPO updates were active but still did not
convert into enough Level3 hard-eval success. v51 therefore starts from the
loop110/v39 3M feed-forward checkpoint, appends deterministic planner-guidance
features to the v5 observation, keeps a 2x256 Tanh PPO Actor as the only action
source, and tests whether route-intent information helps gate/obstacle
conversion. The planner is deployed only as observation computation: no planner
actions, MPC, safety shield, static seed replay, or track modification are
allowed. It must still hard-evaluate on unchanged `config/level3.toml`.

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
