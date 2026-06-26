# v60：不教 PPO 过门，只教它听懂轨迹命令

这次你的判断是对的：v58 如果继续用“过门语义”去训练底层 tracker，很容易把
PPO 带偏。

新的方向是 v60：

```text
planner：负责过门路线和什么时候减速
PPO tracker：只负责跟踪一小段 reference trajectory
```

底层 PPO 要学的是：

```text
给它当前点、下一个点、lookahead 点、期望速度、期望 heading
它能稳定跟过去
该停就停
该慢速通过就慢速通过
不要冲过头
```

它不应该拿这些奖励：

```text
gate pass bonus
finish bonus
aperture crossing bonus
race progress
stage progress
```

这次已经把 loop 里的下一阶段从旧 v58 改成：

```text
v60_reference_command_tracker_no_gate_reward
```

训练还没有启动。下一步应该先做 v60 smoke/checker，确认代码、评估、W&B、旧
checkpoint 兼容都没问题，再考虑 bounded 训练。
