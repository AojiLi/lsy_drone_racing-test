# v61 Brax rollout 速度测试

这次把 SBX 路线排除了。

原因很简单：

```text
SBX 能跑，但太慢，不适合作为主训练路线。
```

我已经删掉：

```text
lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
sbx-rl 依赖
```

然后新增了一个纯 JAX / Brax-style rollout 测速脚本：

```text
scripts/benchmark_v60_brax_rollout.py
```

它不是正式训练，而是测试一件事：

```text
能不能把 v60 tracker 的 rollout 放进 JAX scan 里，
尽量留在 GPU 上跑。
```

这个 benchmark 包含：

```text
policy MLP
action scaling
race env step
v60 dense command reference
command-v3 observation
clean no-gate command reward
```

1024 env x 32 steps 的结果：

```text
稳定后约 0.020s / 32768 steps
约 1.6M env steps/s
```

对比当前 PyTorch fast path：

```text
1M steps 用时 26.34s
约 39.8k env steps/s
```

所以结论是：

```text
纯 JAX/Brax rollout 方向明显值得继续。
```

但注意：这还不是完整 PPO 训练。它还缺：

```text
PPO update
checkpoint 保存/加载
W&B logging
评估脚本兼容
```

下一步应该是：

```text
把这个 rollout 接成真正的 Brax PPO trainer smoke。
```

先 bounded smoke，不要直接长训练。
