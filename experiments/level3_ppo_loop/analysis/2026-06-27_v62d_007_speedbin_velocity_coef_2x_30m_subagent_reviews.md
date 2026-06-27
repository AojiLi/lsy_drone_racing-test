# v62d_007 Subagent Reviews

Date: 2026-06-27

Candidate:

```text
v62d_007_speedbin_velocity_coef_2x_30m
```

## tracker_eval_metrics

Verdict:

```text
No promotion.
```

Best checkpoint:

```text
lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_30m/v62d_007_speedbin_velocity_coef_2x_30m_step_015000000.pkl
```

The 15M milestone is best by balanced score, behavior score, and velocity inside
this candidate:

```text
reward=-2.5724
position=0.2026
cross_track=0.1710
velocity=0.7943
done=0.0
action_delta=0.0000875
balanced=-3.8301
```

It improves spatial tracking versus the plain v62c 7M default, but fails the
velocity-obedience objective. Velocity is worse than v62c 7M default, worse
than v62d_003, worse than v62d_004, and worse than v62d_006. The only velocity
win is a small 2.9% improvement against the same-distribution v62c 7M
speed-bin baseline, below the 10%-15% promotion threshold.

Late drift is clear. The final/30M checkpoint falls to:

```text
reward=-3.1670
position=0.2596
cross_track=0.2329
velocity=1.0491
action_delta=0.000456
```

## tracker_wandb_ppo

Verdict:

```text
PPO plumbing is healthy, but do not continue this candidate.
```

Evidence:

```text
steady_state_steps_per_s ~= 1.24M
steady_state_vs_pytorch ~= 31x
action_distribution = tanh_squashed_gaussian
sample_clip_fraction = 0.0
stored_vs_env_logprob_abs_mean ~= 3e-7
```

The action path is clean. The failure is not action clipping or tanh log-prob
plumbing.

The PPO curve becomes unstable late:

```text
last-50-update KL mean ~= 0.0317
last-50-update clip_fraction mean ~= 0.242
KL spike ~= 0.2415 near 28.5M
clip_fraction spike ~= 0.591 near 28.5M
```

The run's own pre/post deterministic eval worsened despite spatial learning:

```text
reward: -6.2637 -> -9.1786
velocity_error: 0.5682 -> 1.0496
done_mean: 0.0056 -> 0.0227
```

Use the 15M checkpoint only as this candidate's best comparison point. Do not
extend v62d_007 or use the final checkpoint.

## tracker_structure_research

Verdict:

```text
Do not promote v62d_007. Switch back to Family C generator velocity distribution.
```

The best checkpoint audit is clean:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.23e-7
```

The failure is behavioral. Combining `speed_bin_balanced` with blunt
`command_vel_error_coef=1.2` did not improve velocity obedience. The next
candidate should not add another reward coefficient combination.

Recommended next candidate:

```text
v62d_008_velocity_contrast_constant_speed_generator
```

Use a single new generator-profile knob, such as:

```text
command_generator_profile=velocity_contrast_constant_speed
```

Keep:

```text
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
value_target_scale=1.0
command_vel_error_coef=default
num_envs=1024
num_steps=32
train_from_scratch=true
no gate/aperture/race/obstacle/planner-phase actor inputs
```

Hypothesis:

```text
speed_bin_balanced teaches spatial tracking but does not force enough velocity
contrast. The next generator should over-sample longer constant-speed windows
and paired low/medium/high speed variants on similar geometry while preserving
brake ramps and low-speed-through behavior.
```

Builder/checker is required because this adds generator semantics.
