# v55 hover attempt004 做了什么

这一轮成功了：`hover` 第一关已经通过。

之前的问题是：PPO 从零学 hover 时，会学成“安全地停在错误地方”。所以这轮换了策略：

```text
先用一个简单 PD controller 当老师
把老师的 hover 动作行为克隆进 PPO actor
再从这个 checkpoint 做 1M PPO 微调
```

结果：

```text
成功率: 100%
crash: 0%
平均位置误差: 约 0.059m
p90 位置误差: 约 0.085m
平均速度: 约 0.035m/s
动作变化: 很小
```

通俗讲：现在底层 PPO tracker 已经会第一件最基础的事：

```text
给它一个固定 reference point，它能稳稳地飞过去并悬停住。
```

这个结果还不代表可以跑 Level3。它只说明底层 tracker 的第一个能力过关了。
下一关是 `point_hold`：不只是原地悬停，而是到一个点之后停住、别冲过头。

下一步：

```text
用 hover 通过的 checkpoint 初始化 point_hold 训练
跑 2M steps
评估 500k / 1M / 1.5M / final
只有 point_hold gate 通过后，才进入 point_reach
```
