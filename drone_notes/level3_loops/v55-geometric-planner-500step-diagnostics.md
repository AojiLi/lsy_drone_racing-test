# v55 几何 planner 500-step 诊断

这次没有训练 PPO，只是把 planner + tracker 在 Level3 上多跑一会儿，并且记录每一步轨迹。

结果：

```text
20 / 20 seeds 都朝第一道门推进
3 / 20 seeds 通过 gate0
15 / 20 最后是 contact
5 / 20 跑满 500 steps 但没过 gate0
config/level3.toml 没改
```

通俗讲：现在不是“飞不动”，而是“能飞到门附近，但大多数没从门洞中间穿过去”。

成功的 seed 在穿门附近，Y/Z 偏差大概只有 `0.10m-0.19m`。失败但已经过了门平面的 seed，Y/Z 偏差经常是 `0.5m+`。所以主要问题不是时间不够，也不是 PPO 完全不会跟点，而是 planner 给的门前对准和穿门轨迹还不够保守。

下一步应该先调 planner，不要急着长训练：

```text
align 阶段多停一会儿
pre-gate 点再稳一点
cross 速度更慢
如果已经靠近门平面但偏得很远，先退回门前重新对准
没有真正切到下一个 gate 前，不要太早进入 recover
```

一句话：这个方向是对的，但现在要先把几何 planner 的“慢、稳、对准”做好，再让 PPO tracker 去跟。
