# v55 hover attempt002 做了什么

这轮不是直接跑 Level3 赛道，而是在训练底层 PPO tracker 的第一关：

```text
给 PPO 一个目标点
PPO 输出 roll / pitch / yaw / thrust
看它能不能稳定悬停到目标附近
```

训练已经改成了并行 PPO：

```text
1024 个环境 x 32 步 = 每次更新 32768 条样本
```

这一点是好的，速度已经不再是单环境那种慢跑。

但是 hover 第一轮没有通过。最好的 checkpoint 是 500k：

```text
成功率: 0%
撞毁率: 0%
平均位置误差: 约 0.65m
平均速度: 约 0.003m/s
动作变化: 很小
```

通俗说：飞机学会了“很安静地不乱动”，但没有学会“飞到目标点附近”。

问题不是训练太短这么简单。因为 500k 时它最稳定，继续到 750k 和 final
反而变成 100% crash。更像是当前 hover 任务本身设计不对：

- 环境从地面附近开始；
- hover 目标在大约 0.65m 高度；
- 但 reference 又告诉它期望速度是 0；
- reward 长时间都是负数，早撞有时反而不像长期活着那么亏。

所以下一步不是继续同样配置加步数，而是修 hover 训练方式：

```text
先从空中小误差 hover 开始
离目标远时给朝目标的 desired velocity
靠近目标后再要求低速悬停
提高 crash penalty
补上 PPO KL / explained variance 日志
```

下一轮名字：

```text
v55_hover_airborne_error_curriculum_attempt003
```

这仍然不改 `config/level3.toml`，只是改 tracker 的训练小环境和底层
hover 课程。
