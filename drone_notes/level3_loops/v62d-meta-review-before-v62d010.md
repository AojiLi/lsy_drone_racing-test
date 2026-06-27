# v62d Meta-Review Before v62d_010

这次不是继续盲跑训练，而是停下来回答一个问题：

```text
为什么 v62d 已经跑了 9 个候选，还是没有超过 v62c 7M？
```

结论很清楚：

```text
v62d_008 会听速度，但飞得不够准。
v62d_009 飞得准一点，但又不听速度了。
```

更具体地说，`v62d_008` 是目前最有价值的信号。它把速度误差从
`0.7397` 拉到 `0.5708`，提升约 `22.8%`。这说明 PPO tracker 不是完全学
不会速度命令。

但它的问题是 pass-through 阶段飞散了：

```text
pass-through position error 变差 26.7%
pass-through cross-track error 变差 43.3%
```

也就是它更会按速度飞了，但路线贴合变差。

`v62d_009` 试图用更短、更保守的 generator 把路线拉回来。它确实把空间误差
拉回了一些，但代价是速度提升没了。15M 的最好点甚至比 v62c 速度更差。

所以下一步不是：

```text
继续缩短 generator
继续加全局速度 reward
继续调 value scale
```

而是：

```text
保留 v62d_008 的 velocity contrast generator，
只加一个“别偏离轨迹太多”的通用 cross-track reward 保护。
```

下一候选是：

```text
v62d_010_velocity_contrast_cross_track_guard
```

它要做的事：

```text
command_generator_profile = velocity_contrast_constant_speed
trajectory_cross_track_coef = 1.8  # 从 1.2 提高
```

通俗讲：

```text
保留“按速度飞”的训练分布，
但更强地惩罚横向偏离小轨迹。
```

这仍然是干净的底层 tracker 训练：

```text
不加 gate reward
不加 aperture reward
不加 race progress
不改 level3.toml
不让 PPO 学过门
```

下一步先做 builder/checker support，让训练脚本能安全传入这个 reward 系数，
然后再从零跑 v62d_010 的 30M。
