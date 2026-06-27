# v62d-010 cross-track reward guard

这轮还是底层 PPO tracker，不是直接跑 Level3 完赛。

这次想验证一个很具体的问题：

```text
v62d_008 速度听话，但路线有点散。
那能不能保留 v62d_008 的速度训练方式，
再加一点 cross-track 约束，让它既听速度，又别偏离轨迹？
```

做法是：

```text
command_generator_profile = velocity_contrast_constant_speed
trajectory_cross_track_coef = 1.8
```

也就是：继续用 v62d_008 那种强速度对比训练，但额外惩罚偏离小轨迹。

## 结果

训练跑了 `30M`，评估了 `5M / 10M / 15M / 20M / 25M / 30M / final`。

这轮内部最好的 checkpoint 是 `5M`：

```text
lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_30m/v62d_010_velocity_contrast_cross_track_guard_30m_step_005000000.pkl
```

和同 profile 的 v62c 7M 对比：

| 指标 | v62c same-profile | v62d_010 5M | 解释 |
|---|---:|---:|---|
| 位置误差 | 0.7297 | 0.6613 | 更好 |
| cross-track | 0.5185 | 0.4946 | 更好 |
| 速度误差 | 0.7954 | 0.9339 | 更差 |
| done | 0.00391 | 0.00586 | 更差 |
| 综合分 | -8.3369 | -8.6649 | 更差 |

30M / final 的速度误差变好了：

```text
velocity error = 0.6061
```

但位置和 cross-track 崩了：

```text
position error = 0.9581
cross-track error = 0.7451
```

## 通俗结论

这轮没有解决核心矛盾。

它表现得像这样：

```text
5M: 跟轨迹比较准，但速度不听话
30M: 速度比较听话，但轨迹跟丢了
```

也就是说，单纯加一个全局 cross-track reward，并不能把
`速度服从` 和 `轨迹精度` 同时保住。

## 训练系统是否有问题

这轮的训练系统本身是可信的：

```text
action clipping = 0
action/logprob 一致性约 3e-7
W&B 正常在线记录
速度约 1.27M env steps/s
```

但 critic 还是很弱：

```text
explained variance 接近 0
value std 很小
return std 很大
```

通俗说：actor 在学一点东西，但 critic 对不同状态的价值判断还是很钝。

## 下一步

不要继续 v62d_010，也不要直接开 v62d_011。

因为现在已经跑完 10 个 v62d 候选，下一步应该先做一个：

```text
10-candidate meta-review
```

把 v62d_001 到 v62d_010 全部横向看一遍，回答：

```text
到底是 reward 冲突？
generator 分布不对？
critic/value 学不好？
还是 PPO 更新方式还要改？
```

当前最好基线仍然是：

```text
v62c 7M
```

v62d_010 的 5M checkpoint 只能当诊断 checkpoint，不能当新的最佳模型。
