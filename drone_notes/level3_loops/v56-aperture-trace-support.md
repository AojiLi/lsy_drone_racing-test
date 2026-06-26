# v56 aperture trace support 小结

这轮没有训练 PPO，也没有换 checkpoint、改 reward、改 observation、加
MPPI；`config/level3.toml` 保持不变。

这轮主要补了诊断能力：在 trace 里加入：

```text
aperture_y
aperture_z
aperture_yz_error
```

它们表示“飞机在门坐标系里，离真正门洞中心还有多远”。同时加了测试，
确认这个误差公式是对的。

固定 smoke 还是：

```text
seeds 101-120
每个 seed 500 steps
checkpoint：v55 zigzag 合格 tracker
赛道：原始 config/level3.toml
```

结果：

```text
gate0 pass：2/20
first-gate progress：19/20
contact：20/20
all finite：true
```

旧的 checker 通过了，但它只说明管线没坏，不代表 v56 目标通过。v56
真正要的是：

```text
gate0 pass >= 10/20
contact <= 8/20
first-gate progress = 20/20
```

这轮明显没达到。

## 关键发现

问题不太像“进入 cross 时没对准门洞”。

进入 cross 时，`aperture_yz_error` 大多在 `0.15-0.18m` 左右，已经算
比较对准了。也就是说，继续只把 Y/Z 阈值调得更严，未必能解决主要问题。

更像的问题是：

```text
planner 给出的 reference / phase 切换 / desired_speed
↓
底层 PPO tracker 实际跟不上
↓
飞机在门前或门附近 contact
```

尤其是 phase4 里，planner 虽然希望慢下来，但实际 gate-local X 速度
仍然偏高。

## 当前决策

这轮以后，v56 不应该继续自动拧单个小旋钮了。因为 Task1、Task3、Task2
都没有把 gate0 pass 从 `2/20` 拉起来，Task4 只是修正语义。

所以当前决策是：

```text
hold_for_user_review
```

也就是先停下来给你审阅，而不是在同一个 goal 里继续自动开下一条结构线。

## 如果继续，下一步候选

下一步建议进入：

```text
v57_reference_geometry_tracker_interface_audit
```

也就是不要继续盲调单个阈值，而是专门审计和重设计：

```text
planner reference geometry
PPO tracker 跟踪接口
phase 切换时机
reference 是否跳变太大
desired_speed 是否真的能让 tracker 慢下来
```

通俗说：现在不是继续问“门洞阈值再调多少”，而是要看“planner 给
tracker 的小路本身，是不是 tracker 能稳定跟住的那种小路”。
