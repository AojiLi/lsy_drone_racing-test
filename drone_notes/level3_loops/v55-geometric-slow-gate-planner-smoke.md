# v55 几何 planner 正式 smoke 结果

这次正式跑的是：

```text
GeometricSlowGatePlanner
-> zigzag 阶段通过的 PPO tracker checkpoint
-> unchanged config/level3.toml
-> seeds 101-120
```

结论很明确：**planner smoke 通过了。**

关键数字：

```text
20 / 20 seeds 有 first-gate progress
1 / 20 seeds 通过 gate0
gate0 pass seed = 113
early termination = 2 / 20
action 全部 finite
config/level3.toml 没有改
```

通俗讲，这说明现在这个闭环不是“原地瞎动”了：

```text
几何 planner 给 reference
PPO tracker 跟 reference
无人机确实朝第一道门推进
并且至少有一个 seed 真正过了第一道门
```

但这还不是 Level3 已经能完赛。它只是证明了第一版几何 planner + tracker 的接口是活的，并且已经达到当前 planner smoke 的晋级门槛。

下一步不应该直接宣布成功，也不应该立刻说要 MPPI。更合理的是进入：

```text
manual_long_level3_training_review
```

也就是先决定下一轮到底要看什么：

- 要不要把 planner smoke 的 horizon 从 150 steps 拉长；
- 要不要保存失败 seed 的 reference 轨迹方便看；
- cross phase 是否太快；
- pre-gate align 是否还不够稳；
- 是否需要专门训练 tracker 跟 planner 生成的轨迹。

一句话：这一步证明“路子是通的”，但还没有证明“能稳定跑完整个 Level3”。
