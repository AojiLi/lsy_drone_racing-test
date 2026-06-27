# v62b PPO 信号审计

这次不是继续调 reward，而是先查 PPO 自己学东西的信号有没有问题。

结论很明确：现在默认设置下，PPO 的学习信号不干净，所以先别调 reward。

通俗说，现在的问题像这样：

```text
PPO 想输出一个动作
动作太大，被环境 clip 到 [-1, 1]
环境实际执行的是 clipped 后的动作
但 PPO 训练时还在按原始 unclipped 动作算 logprob
```

也就是：

```text
PPO 以为自己做了 A
环境实际执行了 B
然后 PPO 根据 A 的概率去更新
```

这会让训练信号变脏。

关键数字：

```text
默认 initial_log_std = -0.5
action std = 0.6065
34.34% 的 step 至少有一个动作维度被 clip
raw logprob 和 clipped-action logprob 平均差 0.3427
advantage mean/std = -36.41 / 33.90
```

旧的 v62 1M checkpoint 也没有变好：

```text
40.12% 的动作有 clip
logprob mismatch = 0.3968
std 仍然约 0.611
```

所以之前 1M 训练后 eval 变差，不一定是 reward 写错了，更可能是 PPO
一开始探索太猛，训练时记录的 action/logprob 和环境真实执行的 action
不一致。

更好的设置是：

```text
initial_log_std = -2.0
std = 0.1353
clip fraction = 0
logprob mismatch = 0
advantage scale 也正常
```

下一步应该是：

```text
先修 v62b PPO 信号
不要动 reward
不要改 observation
不要改 level3.toml
```

具体就是：

```text
1. 用 initial_log_std=-2.0 跑新的 bounded 1M
2. 降低或关闭 entropy pressure
3. 检查 action/logprob 是否严格一致
4. 如果 1M 还是不学，再讨论 reward scale / value normalization
```

一句话：

**现在不是“怎么奖励它”的问题，先要保证 PPO 真正在学习环境实际执行的动作。**
