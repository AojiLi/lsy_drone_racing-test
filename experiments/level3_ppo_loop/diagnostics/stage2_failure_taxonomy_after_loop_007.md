# Level3 PPO Stage 2 Diagnostic: Failure Taxonomy After Loop 007

## Scope

This is a diagnostic-only Stage 2 artifact. It does not change reward,
observation, PPO, training, evaluator, or environment code.

Inputs:

- Global incumbent:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Latest Stage 1 probe:
  `lsy_drone_racing/control/checkpoints/level3_loop_007_custom_axis_dominant_controlled_probe/level3_loop_007_custom_axis_dominant_controlled_probe_final.ckpt`
- Config: `config/level3_dr.toml`
- Seeds: `1..40`
- Diagnostic command family:
  `pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py --mode single --config level3_dr.toml ...`

## Result

Both checkpoints still fail the hard task completely under the crash-taxonomy
diagnostic:

| Checkpoint | Episodes | Success | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| `001_baseline_final` | 40 | 0 | 40 | 0 |
| `007_final` | 40 | 0 | 40 | 0 |

The failures are concentrated before reliable mid-track traversal. Most crashes
occur while the active target gate is `0` or `1`.

## Crash Distribution

### Global Incumbent: 001 Baseline Final

Artifacts:

- Episodes CSV:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_001_baseline_final_crash_taxonomy_episodes.csv`
- Summary JSON:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_001_baseline_final_crash_taxonomy_summary.json`
- Hotspot plot:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_001_baseline_final_crash_taxonomy_hotspots.png`

Crash targets:

- target gate `0`: `17`
- target gate `1`: `17`
- target gate `2`: `6`

Likely objects:

- `gate_0_top`: `15`
- `obstacle_0`: `6`
- `obstacle_1`: `4`
- `gate_0_left`: `3`
- `gate_0_stand`: `2`
- `gate_1_right`: `2`

Mean local crash position relative to active target gate:

- target gate `0`: `x=-0.277`, `y=-0.148`, `z=-0.314`
- target gate `1`: `x=-1.968`, `y=-0.441`, `z=-0.281`
- target gate `2`: `x=-1.441`, `y=-0.160`, `z=0.496`

Interpretation: many crashes happen before crossing the active target gate
plane. The target-gate-local `x` coordinate is negative on average for all
crash groups, including a large negative offset for target gate `1`.

### Latest Probe: 007 Final

Artifacts:

- Episodes CSV:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_007_final_crash_taxonomy_episodes.csv`
- Summary JSON:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_007_final_crash_taxonomy_summary.json`
- Hotspot plot:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_007_final_crash_taxonomy_hotspots.png`

Crash targets:

- target gate `1`: `22`
- target gate `0`: `15`
- target gate `2`: `3`

Likely objects:

- `gate_0_top`: `11`
- `obstacle_0`: `7`
- `gate_0_right`: `4`
- `gate_1_left`: `3`
- `obstacle_1`: `3`
- `gate_0_left`: `2`
- `gate_0_stand`: `2`
- `gate_1_right`: `2`

Mean local crash position relative to active target gate:

- target gate `0`: `x=-0.335`, `y=-0.176`, `z=-0.369`
- target gate `1`: `x=-1.458`, `y=-0.359`, `z=-0.217`
- target gate `2`: `x=-1.167`, `y=-0.230`, `z=0.504`

Interpretation: 007 shifts more crashes to target gate `1`, but it still does
not produce finishes, and the active-gate-local `x` remains negative on
average at crash. The axis-dominant reward probe did not solve approach-plane
crossing.

## Controller Parity Check

`ppo_level2_inference.py` and `ppo_level3_inference.py` were compared. Their
controller logic is effectively identical; the meaningful source difference is
the default `MODEL_NAME` constant and comments.

Relevant implication:

- The selected-checkpoint evaluator currently injects checkpoints through
  `ppo_level2_inference.MODEL_NAME`.
- `config/level3_dr.toml` points to `ppo_level3_inference.py`, whose default
  checkpoint remains `checkpoints/level3_DR_initial/level3_DR_initial_step_040000000.ckpt`.

This narrows the evaluator/deploy parity risk. The likely parity issue is not
different observation/action logic between the two inference files; it is that
deploy-style execution via `level3_dr.toml` may silently use the hardcoded
initial checkpoint unless checkpoint injection is explicit.

## Diagnostic Conclusions

1. More reward coefficient search is unlikely to be the next best use of time.
   The policies crash before stable active-gate traversal.
2. The next structural review should focus on learnability and task geometry:
   first-gate approach distribution, target-gate plane crossing, obstacle/gate
   collision geometry, and training difficulty staging.
3. A deploy/evaluator checkpoint-injection check should be done before any
   Stage 2 training change, so future evidence is tied to the intended
   checkpoint and controller path.
4. The existing crash taxonomy is useful but limited: hotspot plotting uses
   nominal config gate positions, while Level3 randomizes track geometry. The
   JSON/CSV rows based on actual episode gate positions should be treated as
   the stronger evidence.

## Proposed Next Stage 2 Work

Do not start another train/eval chunk yet.

Recommended next artifact:

- A Stage 2 proposal packet for a narrow diagnostic change, not a training
  change. The strongest candidate is an evaluator/deploy parity check plus
  first-gate geometry sampler:
  - verify `ppo_level3_inference.py` can be run with explicit checkpoint
    injection;
  - sample Level3 randomized first-gate geometry relative to drone start;
  - summarize whether early crashes line up with extreme first-gate approach
    geometries.

Only after that packet should a structural training change be proposed.
