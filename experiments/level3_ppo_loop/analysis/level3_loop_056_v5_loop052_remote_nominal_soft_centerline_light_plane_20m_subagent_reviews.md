# Loop056 Subagent Reviews

Date: 2026-06-21

Scope:

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry and randomization remain unchanged.
- The latest analyzed trial is
  `level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m`.

## evaluator_metrics

Key finding:

Do not mature loop056. No recent branch beats loop052 on hard eval. The next
trainable branch should start from loop052 final unless a new decision packet
explicitly names a structural lane that justifies another start point.

Evidence:

- Current best loop052 final: success `0.20`, crash `0.80`, mean gates `1.40`,
  mean successful time `6.975s`.
- loop056 best 5M: success `0.15`, crash `0.85`, mean gates `1.20`,
  time `6.96s`.
- loop056 final: success `0.10`, crash `0.90`, mean gates `1.35`.
- Episode comparison shows reshuffling, not improvement: gate count improved on
  `2/20` seeds, worsened on `3/20`, and stayed unchanged on `15/20`.
- loop053 tied success at `0.20` but had lower gates; loops054-056 peaked at
  `0.15`.

Recommended next action:

`hold_for_more_analysis` or `launch_named_structural_lane`, but not
continuation of loop056 and not the analyzer's aggressive gate-acquisition
command.

Evaluator promotion criterion for the next chunk:

- success `>=0.25` on 20 seeds; or
- success `0.20` with mean gates `>1.40`, crash `<=0.80`, and mean successful
  time `<=7.0s`.

Rollback:

Rollback to loop052 if the next branch peaks at `<=0.15` success, or ties
`0.20` success with lower gates or worse crash than loop052.

## wandb_ppo_diagnostics

Key finding:

Loop056 is a W&B/PPO non-conversion run. Training signals moved, but the policy
did not convert them into hard-eval progress. Abandon the soft-centerline
light-plane lane and fall back to loop052 as the current best.

Evidence:

- Best loop056 checkpoint: 5M, success `0.15`, mean gates `1.20`, crash `0.85`,
  mean success time `6.96s`.
- Global best loop052 remains stronger: success `0.20`, mean gates `1.40`,
  crash `0.80`.
- `train/reward` improved from `-233.87` to `1.28`, but `train/total_reward`
  worsened to `-35216.57`; reward gain did not transfer.
- Race metrics stayed flat: `passed_gate_rate` tail `0.00834`,
  `finished_rate` tail `0.000295`, `gate_plane_cross_rate` tail `0.002075`.
- PPO was stable but under-moving: `approx_kl` tail `0.000247` versus
  `target_kl=0.03`, `clipfrac=0`, and policy loss near zero.
- Entropy rose to `4.67`; explained variance was acceptable at tail `0.763`;
  SPS was healthy at about `6.68M`, so throughput is not the blocker.

Recommended next action:

`hold_for_more_analysis`. No next training command is approved from W&B/PPO
evidence alone.

Rollback:

Rollback is already triggered for loop056 because success stayed `<=0.15`,
crash stayed `>=0.85`, and gate/finish/plane-cross W&B signals were flat.

## structure_research_synthesis

Key finding:

Launch one new structural observation lane:
`v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`.

The next defensible axis is not more reward scale, PPO pressure, or
soft-centerline shaping. It is giving the policy explicit current-gate corridor
versus obstacle geometry while keeping loop052 reward/PPO/controller settings
fixed.

Evidence:

- loop052 remains global best: `0.20` success, `1.40` mean gates, `0.80` crash.
- loop053 unchanged maturation, loop054 gate pressure, loop055 PPO pressure,
  and loop056 light soft-centerline all failed to beat loop052.
- loop056 vs loop052 taxonomy still concentrates failures at gate0/gate1 and
  nearby obstacles.
- loop051/054 already falsify aggressive and mild gate-pressure retunes.
- high-scale frame/direct/soft-centerline lanes already showed reward-structure
  collapse or flat pass conversion.
- v6/v7 changed gate semantics or phase/progress, but did not add explicit
  obstacle-relative gate-corridor features.

Recommended next action:

`launch_named_structural_lane`, after a new packet defines
`v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`.

Required constraints:

- Attach the loop056 analysis packet.
- Attach the loop056 hold decision packet.
- Attach a new v8 structural/research packet.
- Start from loop052 final.
- Hard-evaluate on unchanged `config/level3_dr.toml`.
- Use `--max-iterations 1`, W&B logging, 30M steps, and 5M checkpoints.

Rollback:

Rollback to loop052 and hold if v8 best stays `<=0.15` success, crash stays
`>=0.85`, mean gates do not reach at least `1.40`, or taxonomy still shows the
same early gate/obstacle crash pattern with flat W&B pass/finish/plane-cross
conversion.
