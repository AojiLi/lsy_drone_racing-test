# v62d Meta-Review Before v62d_010

Date: 2026-06-27

## Purpose

State required a pause before launching `v62d_010`:

```text
Compare v62c 7M and v62d_003/v62d_004/v62d_008/v62d_009 per-command failures
and critic/value diagnostics, then choose one next knob.
```

This is a generic reference-command tracker review, not a Level3 hard eval.
It does not modify `config/level3.toml`, does not approve 60M+ maturation, and
does not add gate/aperture/race/finish/stage rewards.

## Inputs

Primary evidence:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62c_milestone_value_velocity_review.md
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_003_velocity_coef_2x_30m_analysis.md
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_004_speed_bin_balanced_generator_30m_analysis.md
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_008_velocity_contrast_constant_speed_generator_30m_analysis.md
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_009_velocity_contrast_spatial_guarded_generator_30m_analysis.md
experiments/level3_ppo_loop/v62d_candidates/registry.md
```

Additional per-command deterministic eval was generated for this meta-review:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_meta_per_command_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_meta_per_command_eval.csv
```

Protocol:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval_rollouts: 16
action_distribution: tanh_squashed_gaussian
```

The per-command eval uses the same checkpoint action path and splits metrics by
`pass_through`, `hold_or_brake`, `low_speed_through`, and `recover_speed`.

## Frontier

The standing comparison frontier remains:

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Frontier metrics:

| metric | v62c 7M |
|---|---:|
| reward | -4.8459 |
| command position error | 0.6573 |
| cross-track error | 0.5214 |
| command velocity error | 0.7397 |
| done mean | 0.00391 |
| balanced score | -7.5365 |

## Candidate Pattern

| candidate | best checkpoint | main result |
|---|---|---|
| `v62d_003` | 20M | velocity coefficient 2x improved velocity only `2.4%`; action delta worsened about `7.9x` |
| `v62d_004` | 5M | speed-bin generator greatly improved spatial metrics on its distribution, but velocity was still worse than v62c default and action delta worsened |
| `v62d_008` | 30M | first real velocity breakthrough: velocity improved `22.84%`; position worsened `20.84%` |
| `v62d_009` | 15M | spatial guard restored position/cross-track, but velocity became `5.59%` worse than v62c |

The useful signal is not that all generator work failed. It is more specific:

```text
v62d_008: velocity obedience can be learned, but spatial tracking loosens.
v62d_009: spatial constraints can be restored, but they erase the velocity gain.
```

## Per-Command Findings

### v62d_003: reward scalar is too blunt

Against v62c on the default profile:

| command | position change | velocity change | cross-track change |
|---|---:|---:|---:|
| all | `-2.9%` | `-2.4%` | `-3.7%` |
| pass-through | `+1.0%` | `+0.6%` | `+1.3%` |
| hold/brake | `-1.3%` | `-4.8%` | `-0.8%` |
| low-speed-through | `-6.7%` | `-2.8%` | `-12.4%` |
| recover | `-5.1%` | `-2.0%` | `-5.9%` |

Doubling the global velocity coefficient made small broad improvements, but it
did not create the `10%-15%` velocity improvement required for promotion and
it worsened action smoothness. Do not repeat blunt global velocity weighting as
the next single knob.

### v62d_004: speed-bin generator helps geometry but not speed

Against v62c evaluated on the same speed-bin profile:

| command | position change | velocity change | cross-track change |
|---|---:|---:|---:|
| all | `-5.9%` | `+18.5%` | `-3.0%` |
| pass-through | `-17.5%` | `+6.4%` | `-24.6%` |
| hold/brake | `+22.3%` | `+58.4%` | `+73.6%` |
| low-speed-through | `+19.4%` | `+28.4%` | `+25.6%` |
| recover | `-13.8%` | `+6.6%` | `-14.6%` |

The aggregate spatial result looked attractive because pass-through and some
recover geometry improved, but the command split shows hold/brake and
low-speed-through got much worse. This generator is not the right base for the
next candidate.

### v62d_008: velocity signal is real, spatial looseness is concentrated

Against v62c evaluated on the velocity-contrast profile:

| command | position change | velocity change | cross-track change |
|---|---:|---:|---:|
| all | `+8.9%` | `-28.2%` | `+5.1%` |
| pass-through | `+26.7%` | `-10.6%` | `+43.3%` |
| hold/brake | `-1.6%` | `-56.0%` | `-15.4%` |
| low-speed-through | `-48.0%` | `-44.7%` | `-59.7%` |
| recover | `-15.6%` | `-27.1%` | `-20.2%` |

This is the clearest evidence in the search. `v62d_008` improves the hard
parts of speed obedience, especially hold/brake, low-speed-through, and
recover. Its failure is concentrated in pass-through spatial tracking:

```text
pass-through position error worsens 26.7%
pass-through cross-track error worsens 43.3%
```

That points to a spatial tracking guard for moving segments, not another
velocity reward scalar and not another generator contraction.

### v62d_009: spatial guard erases the velocity breakthrough

Against v62c evaluated on the spatial-guarded profile, the best balanced
`15M` checkpoint:

| command | position change | velocity change | cross-track change |
|---|---:|---:|---:|
| all | `-4.0%` | `+3.5%` | `-6.1%` |
| pass-through | `-5.0%` | `+1.5%` | `-7.9%` |
| hold/brake | `+1.3%` | `+9.7%` | `+2.9%` |
| low-speed-through | `-3.3%` | `+3.8%` | `-2.2%` |
| recover | `-3.4%` | `+1.2%` | `-2.4%` |

The `30M` checkpoint recovers some velocity but collapses spatially:

| command | position change | velocity change | cross-track change |
|---|---:|---:|---:|
| all | `+33.8%` | `-7.0%` | `+42.9%` |
| pass-through | `+23.2%` | `+0.0%` | `+33.0%` |
| hold/brake | `+30.6%` | `-25.1%` | `+61.8%` |
| low-speed-through | `-14.5%` | `-24.8%` | `-20.8%` |
| recover | `-3.7%` | `-16.9%` | `-6.0%` |

This says the generator-only spatial guard is too coarse. It can restore
position at 15M, but it removes the velocity-contrast training signal. At 30M,
velocity improves modestly only after pass/hold spatial behavior degrades.

## Critic/Value Diagnostics

The near-constant critic pattern is repeated:

| run | value std | return std | note |
|---|---:|---:|---|
| `v62d_004` final train | ~0.0015 | ~31.34 | explained variance near zero |
| `v62d_008` best audit | ~0.00081 | ~5.76 | action/logprob ok, critic nearly flat |
| `v62d_009` best audit | ~0.00298 | ~4.86 | action/logprob ok, critic nearly flat |
| `v62d_009` final train | ~0.00252 | ~41.07 | explained variance about `5.45e-5` |

This is a real PPO-quality issue, but it is not the best next single knob:

```text
v62d_001/v62d_002/v62d_005 already tried value-target scaling variants.
They improved or changed critic scale in places, but did not produce a better
tracker frontier.
```

The immediate behavioral bottleneck is more specific than "critic weak":

```text
preserve v62d_008's speed obedience while preventing pass-through spatial drift.
```

Critic/value work should remain a follow-up family if a spatial reward guard
still fails, or if it blocks a candidate that otherwise clears behavior gates.

## Decision

Launch one focused next candidate:

```text
v62d_010_velocity_contrast_cross_track_guard
```

Family:

```text
E_best_of_family_combination
```

Hypothesis:

```text
Keep v62d_008's velocity-contrast constant-speed generator, because it is the
only candidate that produced a real velocity breakthrough. Add one generic
spatial tracking reward guard for moving trajectory segments by increasing
trajectory_cross_track_coef from 1.2 to 1.8. This should reduce pass-through
cross-track drift without erasing the velocity contrast signal through another
generator contraction.
```

Exact next knob:

```text
command_generator_profile=velocity_contrast_constant_speed
trajectory_cross_track_coef=1.8
```

Keep unchanged:

```text
action_distribution=tanh_squashed_gaussian
actor observation=level3_reference_tracker_command_v3
value_target_scale=1.0
num_envs=1024
num_steps=32
num_minibatches=4
update_epochs=1
config/level3.toml unchanged
no gate/aperture/race/finish/stage rewards
no gate/obstacle/planner-phase actor inputs
```

Because the current trainer only exposes `--command-vel-error-coef`, v62d_010
needs a builder/checker support step before training. The support step should
add a narrow generic reward-coefficient override path for
`trajectory_cross_track_coef`, record it in checkpoint metadata and audit
metadata, run py_compile/checks, run a small support smoke, and verify
`config/level3.toml` remains unchanged.

## Non-Decisions

Do not launch 60M+ maturation now.

Do not promote `v62d_008` despite its velocity gain, because it violates the
position guardrail.

Do not continue `v62d_009` as-is. Its best balanced checkpoint loses velocity,
and its best velocity checkpoint has large spatial collapse.

Do not add gate/aperture/race/finish/stage rewards. The proposed coefficient is
a generic moving-trajectory cross-track reward already present in the clean
tracker reward family.
