# v60 bounded smoke：管线通了，但还不能判断学没学会

这次跑的是 v60 的短 smoke，不是正式训练。

它验证的是：

```text
训练脚本能跑
W&B 能记录
checkpoint 能保存
evaluator 能加载
stage gate 能检查
v60 的干净 observation layout 确实在用
```

这次 checkpoint 是：

```text
lsy_drone_racing/control/checkpoints/v60_reference_command_no_gate_reward_smoke/v60_reference_command_no_gate_reward_smoke_final.ckpt
```

W&B 地址：

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v60_reference_command_no_gate_reward_smoke_20260626
```

关键结果：

```text
all_finite = true
checkpoint_backed = true
observation_layout = level3_reference_tracker_command_v3
obs_dim = 56
四种 command 都覆盖到了
gate / aperture reward 系数是 0
```

stage gate 没过，这是正常的，因为这次只训练了 4096 步。这个步数只能检查代码和
流程，不能判断 PPO 是否真的学会了。

通俗说：

```text
这次不是考试成绩不好
而是确认考场、卷子、答题卡、监考系统都正常
```

下一步才应该跑真正的 bounded maturation，比如 8M 步、1024 并行环境、每 1M
保存 checkpoint，然后看哪个 milestone 最好。

这次没有改 `config/level3.toml`，也没有启动 Level3 长训练。
