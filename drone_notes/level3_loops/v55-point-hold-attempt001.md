# v55 point_hold attempt001 做了什么

这一轮也成功了：`point_hold` 第二关已经通过。

它做的事情是：

```text
从 hover 已通过的 checkpoint 出发
训练 PPO 去“飞到一个点，然后停住”
```

结果非常稳：

```text
成功率: 100%
crash: 0%
最终平均位置误差: 约 0.019m
最终 p90 位置误差: 约 0.019m
终点速度: 约 0.0003m/s
overshoot: 0
hold ratio: 约 0.866
```

通俗讲：底层 tracker 现在不只是能在一个点悬停，还能到达目标点之后停住，
没有明显冲过头。

这对后面的 planner 很重要，因为 planner 以后会给它一串 reference points。
如果它不能到点后刹住，Level3 里接近门和障碍物时就会很危险。

下一步是 `point_reach`：

```text
从 A 点飞到 B 点
要求低 crash、低终点误差、别明显 overshoot，并且能在合理时间内到达
```

这还是底层 tracker 训练，不是直接跑 Level3。
