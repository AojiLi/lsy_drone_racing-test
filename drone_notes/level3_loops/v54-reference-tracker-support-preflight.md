# v54 参考轨迹 Tracker 预检

这轮没有开始长训练。它做的是先把新路线的“骨架”搭起来并验证能不能跑。

通俗说，现在路线变成：

```text
上层 planner 负责想路线
  -> 生成局部参考点 / 期望速度 / 期望朝向
PPO tracker 只负责跟踪这个参考
  -> 输出 roll / pitch / yaw / thrust
```

这比让 PPO 自己同时决定“往哪里飞”和“怎么控制姿态”更简单。PPO 不再需要自己发明全局策略，它更像一个低层飞控/跟踪器。

这次新增了四块：

- `level3_reference_tracker.py`：参考轨迹、65 维 observation、tracker reward、2x256 PPO 网络、训练环境包装。
- `train_level3_reference_tracker_ppo.py`：专门训练这个 tracker 的入口，之后可以接 W&B。
- `level3_reference_tracker_controller.py`：真实 Level3 推理时的 controller 路径。
- `check_level3_reference_tracker_smoke.py`：检查 hover、point、gate-aperture 和 Level3 seeds 101-105 是否能正常跑。

smoke 结果：

- 动作是 finite，没有 NaN；
- observation 和 reward 是 finite；
- `config/level3.toml` 没有改；
- 现在还没有训练好的 tracker checkpoint；
- 所以 `long_training_gate_passed=false`，不能直接开长训。

重点：这次看到的 first-gate 小进展来自未训练网络的短 smoke，不能当作“已经会飞”。它只能说明接口接通了。

下一步应该先做一个小 curriculum：

1. 先训练 hover，让 tracker 学会稳定悬停/起飞。
2. 再训练 point tracking，让它学会追一个局部点。
3. 再训练 gate-aperture tracking，让它学会对准门洞。
4. 拿这个 checkpoint 去跑 Level3 seeds 101-105 smoke。

只有 checkpoint-backed smoke 通过后，才适合开 W&B 长训练。
