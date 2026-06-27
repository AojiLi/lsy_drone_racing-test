# v62d-009 空间保护版速度对比 generator

这轮做的是底层 PPO tracker，不是直接跑 Level3 完赛。

目标很具体：

```text
保留 v62d_008 的速度服从能力
同时把位置误差 / cross-track 拉回来
```

做法是新增一个 generator：

```text
velocity_contrast_spatial_guarded
```

它继续给 PPO 看低速 / 中速 / 高速的对比训练，但把 reference 轨迹距离缩短，并且更早开始减速。通俗说：

```text
v62d_008: 速度信号强，但路线拉得有点散
v62d_009: 速度信号还在，但路线收紧一点
```

## 结果

训练跑了 `30M`，评估了 `5M / 10M / 15M / 20M / 25M / 30M / final`。

最好的是 `15M` checkpoint：

```text
lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_generator_30m/v62d_009_velocity_contrast_spatial_guarded_generator_30m_step_015000000.pkl
```

和当前基线 v62c 7M 对比：

| 指标 | v62c 7M | v62d_009 15M | 解释 |
|---|---:|---:|---|
| 位置误差 | 0.6573 | 0.6570 | 基本一样 |
| cross-track | 0.5214 | 0.4833 | 更好 |
| 速度误差 | 0.7397 | 0.7811 | 更差 |
| done | 0.00391 | 0.00391 | 一样 |
| 综合分 | -7.5365 | -7.5566 | 略差 |

所以这轮没有超过 v62c 7M。

## 通俗结论

这轮说明一件事：

```text
空间保护确实能把路线拉回来，
但也把 v62d_008 那个速度突破削掉了。
```

也就是说，现在 tracker 像在两个能力之间摇摆：

```text
要速度服从 -> 位置 / cross-track 变差
要位置稳定 -> 速度服从变差
```

这不是简单再调一个 generator 就一定能解决的问题。

## 下一步

不建议立刻再跑一个 30M generator-only 候选。

更合理的是先做一个 v62d meta-review，看清楚：

```text
是 critic/value 学不好？
是 generator 分布要分阶段？
是 reward 比例问题？
还是 PPO update 压力问题？
```

当前最好基线还是：

```text
v62c 7M
```

v62d_009 的 15M 只能当诊断 checkpoint，不能当新的最佳模型。
