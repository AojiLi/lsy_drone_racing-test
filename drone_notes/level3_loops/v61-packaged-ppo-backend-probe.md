# v61 成熟 PPO 后端测试

这次做的是一件很具体的事：不要继续自己手写 JAX PPO，而是优先试成熟包。

已经装好并确认可用：

- `sbx-rl 0.27.0`
- `brax 0.14.2`
- `wandb 0.28.0`

我新增了一个 SBX 训练入口：

```text
lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
```

它做的事是：

```text
现有 v60 tracker env
↓
很薄的 SBX VecEnv adapter
↓
SBX 自带 JAX PPO
```

好消息：能跑，W&B offline 能记录，1024 env 的 smoke 也通过了。

坏消息：不快。1024 env、32768 steps 的单更新测试：

```text
SBX + W&B offline: 约 4115 steps/s
SBX 无 W&B: 约 4570 steps/s
```

而之前 PyTorch fast path 大约是：

```text
约 36k steps/s
```

所以结论很清楚：

```text
SBX = 成熟、稳、能减少自写 PPO 风险
但不是 GPU 利用率/训练速度的解法
```

真正可能解决速度的是 Brax，因为 Brax 的 PPO 会希望环境本身就是纯 JAX
`Env`，rollout 和 update 都更容易留在设备上。

下一步最合理的是：

```text
做一个最小 Brax v60 tracker adapter
只跑 smoke
如果速度明显好，再考虑接入正式 loop
```

不要现在就开 SBX 长训练。它能跑，但从速度看，不适合作为主路线。
