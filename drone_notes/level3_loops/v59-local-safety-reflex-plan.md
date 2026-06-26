# v59 局部安全反射思路

这一步先不训练，只把下一条可能路线记录下来。

核心想法是：

```text
上层 planner：决定路线、什么时候减速、接下来跟哪段小轨迹
底层 PPO tracker：主要负责把这段 reference 稳定跟住
局部安全反射：只在快撞门框/障碍物时做一点小修正
```

所以 v59 不是让 PPO 重新学“怎么过 Level3”。PPO 不应该拿 gate pass
bonus、finish bonus、race progress 这类奖励，也不应该靠 target_gate
完整语义自己做路线决策。

更合理的是：

```text
80%-90% 奖励压力：跟 reference、跟速度、跟 heading、动作平滑、该刹车就刹车
10%-20% 奖励压力：快撞障碍物/门框时有安全惩罚
```

当前代码已经有最近障碍物的相对位置、距离、是否可见，也有 obstacle
penalty 和 crash penalty。因此 v59 第一轮不应该盲目大改 observation，而
应该先审计这些现有安全输入是否够用。

下一步仍然是先跑 v58 semantic reference 的 bounded preflight/eval。只有当
v58 证明 reference 已经连续、能表达“刹车/慢穿/恢复”，但还是因为局部碰撞
失败时，再进入 v59。
