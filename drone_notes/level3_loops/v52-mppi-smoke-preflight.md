# v52 MPPI smoke preflight

这轮不是 PPO 训练，也不是 imitation learning。它只是在问一个问题：

MPPI 这个在线采样控制器，自己能不能把 Level3 跑起来？

## 做了什么

新增了两个核心文件：

- `lsy_drone_racing/control/mppi_level3_oracle.py`
  - 一个 MPPI-only 控制器；
  - 直接输出 `[roll, pitch, yaw, thrust]`；
  - 每一步采样很多未来动作序列，用简化模型预测，然后选 cost 最低的一条。
- `scripts/evaluate_level3_controller.py`
  - 一个非 PPO evaluator；
  - 不需要 checkpoint；
  - 可以统计成功率、撞毁率、平均过门数、终止原因、动作是否有限。

也跑了 builder/checker gate。checker 结论是 `ALL GREEN`：

- `config/level3.toml` 没改；
- action 是有限的；
- evaluator 能记录 termination reason；
- MPPI 的结果没有写成 PPO 成绩。

## 现在效果

5 个 smoke seeds：`101-105`

- 完赛率：`0%`
- 平均过门数：`0.80`
- 撞毁率：`100%`
- 最好的一个 seed 到了第 `2` 个门
- 所有 action 都是有限值，没有 NaN

通俗讲：MPPI 现在还远不能通过 Level3，但它已经不是完全乱飞。它能在一些 seed 上过第一门，甚至摸到第二门。

## 目前卡在哪里

主要卡在门附近 contact。

短轨迹显示，控制器能把飞机带到门附近，但门平面附近的高度、垂直速度和穿门时机还不够稳。有时刚过门或贴近门就撞了。

所以现在的问题不是 PPO，也不是 reward，而是 MPPI 控制器本身还需要继续调：

- 更稳地对准门中心；
- 快到门高时提前刹住 z 速度；
- 过门后立刻切下一个目标，不要在门框附近乱修正；
- 之后再考虑障碍物绕行和速度。

## 下一步

继续 MPPI-only tuning。

先不要跑 PPO，不要生成 teacher data，也不要做 full hard eval。当前 MPPI 还低于 PPO best：PPO best 是 `21%` 成功率、`1.66` 平均过门数，而当前 MPPI smoke 是 `0%` 成功率、`0.80` 平均过门数。

下一轮应该优先把第一门、第二门稳定下来，再扩大 seed 范围。
