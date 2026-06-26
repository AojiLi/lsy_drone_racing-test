# v60 command-trajectory smoke

这次重新跑了 v60 的 bounded smoke。

简单说：管线是通的，但模型当然还没学会。

这轮训练只跑了 `4096` steps，相当于一次很短的启动测试，不是正式训练。它的作用是确认：

- 新的 command-trajectory reward 能正常训练；
- W&B 能看到新曲线；
- checkpoint 能保存；
- evaluator 能跑；
- gate checker 能给出结果；
- 没有 NaN / 非法 action；
- 没有改 `config/level3.toml`。

结果：

- checkpoint backed：通过；
- all finite：通过；
- 四种 command 都出现了：通过；
- W&B 已记录新的 `tracker/command_*` 和 `tracker/trajectory_*` 指标；
- stage gate 没过。

stage gate 没过是预期的，因为 4096 steps 太短，不能说明 PPO 学不会。现在的主要失败是：

- 成功率还是 `0`;
- crash rate 是 `1.0`;
- brake/hold 位置误差约 `0.684m`;
- slow-through 位置误差约 `0.646m`;
- brake/hold 速度略高于目标。

通俗讲：飞机已经能跑完整个训练管线，但这个 checkpoint 还只是“刚出生”，不能指望它会跟轨迹。

下一步应该继续同一个 v60 方向，开真正的 8M maturation：

```text
reference_command_no_gate_reward
8M steps
1024 envs x 32 steps
每 1M 保存 checkpoint
W&B 打开
训练完评估所有 milestone
```

现在不应该改 input、reward 或 planner，也不应该进入 Level3 planner integration。先给这个 v60 tracker 正式训练时间。
