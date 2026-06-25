# v54 Tracker 小课程预检

这轮做了真正的 checkpoint-backed preflight，不是长训。

简单说：我先让 PPO tracker 依次练了三个小任务：

```text
hover
  -> point tracking
  -> gate-aperture tracking
```

每段 8192 steps，总共 24576 steps。后面的任务会接着前面的 checkpoint 训练，不是每次从零开始。

W&B 已经有三条 run：

- `v54_tracker_curriculum_hover_20260625`
- `v54_tracker_curriculum_point_20260625`
- `v54_tracker_curriculum_gate_aperture_20260625`

最终 checkpoint 是：

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_curriculum_preflight/v54_reference_tracker_curriculum_gate_aperture.ckpt`

然后我用这个真实 checkpoint 跑了 Level3 seeds 101-105 smoke。

结果：

- 动作都是 finite，没有 NaN；
- checkpoint 确实被加载了；
- 101 和 104 有明显 first-gate 方向进展；
- 所以形式上的 `long_training_gate_passed=true`。

但这里有一个重要问题：

5 个 seeds 都很快 terminated，而且没有任何 seed 真正过 gate 0。

通俗说，现在不是“已经会跑 Level3”，而是：

```text
这条新路线已经接通了，
PPO tracker 会根据 planner reference 输出动作，
但动作还很不稳，容易很快撞/终止。
```

所以我不建议现在直接开一晚上的 Level3 长训。下一步更合理的是继续做 v54 tracker 稳定性小课程，比如更长的 hover/point、降低学习率或动作激进度，然后再要求 smoke 不只是“有前进”，还要“不那么快死”。
