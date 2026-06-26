# v60 30M tracker 训练分析

结论先说清楚：这次 30M 没有通过 v60 tracker 的验收，所以现在不应该直接接 planner 去跑 Level3。

但它不是完全没学会。它学会了一件重要的事：给它连续 reference，它能越来越贴近轨迹。比如 29M 时，刹车点位置误差大约 `0.111m`，慢穿点位置误差大约 `0.079m`，这已经比 1M 好很多。

问题在于它学得有点“猛”。它为了贴近 reference，会用很大的动作变化去修正。结果是：

- 刹车/hold 附近还是会有太多高速步数，`brake_hold_rush_count` 一直远高于要求的 `<= 2`。
- 慢穿阶段有时会停死，`slow_through_stop_count` 在 8M 之后也超过要求。
- 8M 之后虽然位置更准，但 stage success 反而变成 `0`。
- 所有 checkpoint 都没有 crash，说明不是动作 NaN 或控制直接坏掉，而是 command 语义没学稳。

最通俗的理解：

```text
它已经知道“我要去哪里”，
但还没真正学会“什么时候该稳稳刹住、什么时候该低速穿过去、什么时候不要猛打动作”。
```

这次最有参考价值的点：

- `5M`：比较温和，差一点点过部分语义指标，但位置还不够准。
- `15M/29M/final`：位置很准，但动作太激进，刹车/慢穿语义失败。

所以下一步不建议继续同样的 v60 直接长训。更合理的是开一个 v60b/v61：

```text
目标不是继续追求更小位置误差，
而是专门训练 command boundary stability：
该刹车时不要 rush，
该慢穿时不要停死，
command 切换时动作要平滑。
```

仍然保持干净底层 tracker：

```text
不加 gate reward
不加 obstacle reward
不加 progress / finish / aperture bonus
不让 PPO 自己学过门
只教它稳定跟踪 planner 给的轨迹和速度命令
```

一句话：这次 30M 证明路线有价值，但 reward/generator 现在把它推向了“猛追点”，下一步要把它改成“稳稳跟轨迹”。
