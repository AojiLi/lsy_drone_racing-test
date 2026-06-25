# v55 hover attempt003 做了什么

这轮是在 attempt002 失败后做的结构修复：

```text
从空中附近开始训练
离 hover 目标远时给 desired velocity
提高 crash penalty
补 PPO KL / explained variance 日志
```

结果还是没有通过 hover。

关键结果：

```text
final success: 0%
final crash: 0%
final 平均位置误差: 约 1.15m
final 平均速度: 约 0.236m/s
```

通俗说：它不再像之前那样后期 100% crash，但它学成了“安全地停在错误地方”，
不是“回到目标点并悬停”。

W&B 里 `approx_kl` 和 `clipfrac` 不大，说明 PPO 更新本身没有爆炸。
真正难看的是 `explained_variance` 接近 0、value loss 很大，说明 critic
基本没学明白这个长时间 dense negative reward。

更重要的是：一个简单 PD hover controller 可以在同一个 free-space hover
环境里稳定完成任务。所以环境不是不可解，动作接口也不是完全坏掉；是 PPO
从零探索很难自己发现这个局部伺服控制规律。

下一步：

```text
v55_tracker_hover_pd_warmstart_attempt004
```

先用 PD teacher 生成“应该怎么悬停”的动作，行为克隆到 PPO actor，再从这个
checkpoint 开 PPO 微调。这样底层 tracker 先学会最基本的稳定控点能力，再谈
后面的点跟踪、线跟踪、刹车和 planner。
