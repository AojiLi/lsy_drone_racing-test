# v53 hybrid Level2 虚拟门 smoke

这轮做的是一个新的非纯 PPO controller：

```text
上层 planner 生成参考点 / 参考速度 / 期望朝向
-> 包装成 Level2 PPO 看得懂的虚拟局部门
-> Level2 PPO checkpoint 输出 roll / pitch / yaw / thrust
```

它没有改 `config/level3.toml`，也没有把赛道变简单。它也不是 PPO 训练成功，
只是一个 completion-first 的 hybrid controller 尝试。

## 当前结果

在 `level3.toml` 上跑了 validation seeds `101-105` 的 smoke：

- 成功率：0%
- 平均过门数：0
- crash：80%
- timeout：20%
- action finite：100%

也就是说：代码能跑，动作没有 NaN，但行为还不行。

## 通俗解释

现在这个 controller 已经能让飞机起飞并靠近第一门，但最关键的问题是：

```text
到门口了，却没有稳定从门洞中心穿过去。
```

有些版本会在第一门前面犹豫到 timeout；把穿门动作调激进以后，又变成更容易在
第一门附近 contact。说明问题不在于“完全不会飞”，而在于上层 planner 给 Level2
PPO 包装出来的虚拟门，还没有把“门口居中 + 稳定穿过”的语义表达好。

## 为什么没有继续跑 dev 1-20

因为 smoke 只有 5 个 seed，但已经是：

```text
0% success, 0 mean gates
```

这不属于可以升级的结果。继续跑 1-20 只会多花时间确认它现在还不行。

## 下一步

下一轮应该继续修 v53 adapter，而不是训练 PPO：

- 先让第一门前的横向/高度误差更小；
- 在真正穿门前限制接近速度；
- 只有门口居中以后再给 cross reference；
- 加一个逐步 trace，记录每一步的 gate-local 位置、phase、reference 和 action。

目标是先让 `101-105` 至少出现稳定过第一门，再考虑 dev seeds `1-20`。
