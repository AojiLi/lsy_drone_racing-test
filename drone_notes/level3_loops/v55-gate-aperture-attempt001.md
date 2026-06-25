# v55 gate aperture attempt001 做了什么

这一轮是在训练第 11 个 tracker 能力：局部过门。

目标不是完整跑 Level3，而是先让底层 PPO 学会这件小事：

```text
门前点 -> 门洞中心 -> 穿过门平面 -> 门后恢复
```

## 结果

这轮没有通过。

但它不是完全没学会。它学会了：

- 不 crash；
- 很准地对准门洞；
- 平滑地停住。

问题是：它停在门前，没有真正穿过去。

最终 checkpoint 的关键指标是：

```text
valid_aperture_cross_rate: 0%
post_gate_recovery_rate: 0%
crash_rate: 0%
mean aperture yz error: 0.047 m
p90 aperture yz error: 0.027 m
```

通俗说就是：

```text
飞机已经能把自己摆到门洞前面，而且摆得挺准，
但是它觉得“停在这里”就是好答案。
```

## 为什么会这样

三个子 agent 的结论一致：PPO 没崩，训练也不是完全没效果，而是 reward/curriculum 给了它一个错误的局部最优。

当前奖励主要鼓励：

- 靠近 reference 点；
- 对准门洞 Y/Z；
- 保持平滑；
- 不 crash。

但没有足够明确地奖励：

- 从门前穿过门平面；
- 到门后还能恢复。

所以它学成了“门前精准停车”。

## 下一步

不要继续原 reward 加训练步数。下一步改成 attempt002：

```text
v55_gate_aperture_phase_completion_attempt002
```

会做两个小改动：

1. gate-aperture 训练环境从空中近门开始，不再从地面起飞开始；
2. reward 加上穿门和门后恢复相关信号，同时惩罚在门前停太久。

`config/level3.toml` 没有改，最终 Level3 赛道仍然不变。
