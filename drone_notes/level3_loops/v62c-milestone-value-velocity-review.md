# v62c 里程碑速度复查

这次做的事情很简单：把 v62c 这次 10M 训练保存下来的 `1M-9M` checkpoint
和 final 全部重新评估一遍，看哪个最好，以及速度跟踪是从什么时候开始变差的。

结论：

```text
最佳 checkpoint: 7M
路径:
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

为什么是 7M：

- reward 最好；
- 综合分最好；
- 在训练后的 checkpoint 里，速度误差也是最低的；
- done rate 也是最低的一档。

但这里有一个关键问题：7M 只是“这批 checkpoint 里最好”，不是说 tracker 已经合格。

速度问题从两个角度看：

```text
和初始随机策略比:
initial velocity error = 0.6465
1M velocity error      = 0.8826
```

也就是说，从 1M 开始速度跟踪就已经比初始更差了，后面也没有恢复到 initial
以下。

如果只看训练过程内部：

```text
7M velocity error    = 0.7397
8M velocity error    = 0.8798
9M velocity error    = 0.8696
final velocity error = 0.8915
```

所以训练内部的速度峰值在 7M，8M 开始又明显变差。

通俗说，目前 PPO 学到了一些“更接近轨迹”的能力，但是它为了贴近轨迹，牺牲了“按
planner 要求的速度飞”的能力。这对 Level3 planner + tracker 架构是不够的，因为
planner 最需要底层听懂：

```text
慢下来
刹住
低速穿过
再慢慢恢复速度
```

下一步不应该直接从 final 继续长训，也不应该马上开 60M。更合理的是先做一个
`v62d_value_velocity_stabilization_support`：保留 tanh-squashed Gaussian 和干净
tracker 输入，但解决 value/return scale 和 velocity obedience 的问题。之后如果要
继续训练，优先从 7M 这个 checkpoint 做诊断性续训。
