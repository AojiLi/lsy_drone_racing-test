# v55 几何慢速 planner 说明

这次把 Level3 planner smoke 的第一版 planner 定成了：

```text
GeometricSlowGatePlanner
```

它不是 MPPI，也不是 MPC。它不直接输出动作，只输出接下来要跟的 reference points、速度和朝向。动作仍然由底层 PPO tracker 输出。

整体链路还是：

```text
Level3 观测
-> 几何 planner 生成短轨迹
-> PPO tracker 跟踪轨迹
-> roll / pitch / yaw / thrust
```

这个 planner 很保守，分 5 个阶段：

```text
cruise: 远处慢速朝门前飞
slowdown: 接近门前开始减速
align: 门前对准
cross: 穿门
recover: 过门后恢复
```

它还有一个简单的 hysteresis：同一个 gate 内 phase 只往前走，不会因为位置在边界附近抖动就来回切。环境切到下一个 `target_gate` 后，planner 才重置到下一门的巡航阶段。

障碍物处理也先做得很简单：如果可见障碍物离当前 reference segment 太近，就把 waypoint 在 Y/Z 方向轻微偏开。这个不是最终避障算法，只是第一版安全规则。

已经验证：

```text
单元测试 21 passed
ruff passed
untrained micro smoke all_finite=true
zigzag checkpoint micro smoke all_finite=true
config/level3.toml 没有改
```

注意：这两个 micro smoke 只是验证管线不炸，不代表已经会过门。下一步真正要跑的是 `planner_integration_smoke`，用 zigzag 已通过的 tracker checkpoint，在不改 `config/level3.toml` 的情况下跑 seeds 101-120。
