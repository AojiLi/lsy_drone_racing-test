# v60 command-trajectory reward

这轮没有改 input，也没有改 Level3 赛道。

核心变化是：v60 tracker 的 reward 不再只是像“追当前点”那样工作，而是更像“按 planner 给的小轨迹执行命令”。

现在 PPO 看到的还是 56 维 `level3_reference_tracker_command_v3`：

- 自身状态；
- current / next / lookahead 三个 reference 点；
- desired velocity / speed / heading；
- pass、brake、slow、recover 这类通用 command mask；
- last action 和两步历史。

新增的是 reward 里的理解方式：

- moving command：看它有没有沿 `current -> next -> lookahead` 这段小轨迹飞；
- slow-through：看它有没有低速沿轨迹穿过去，而不是停死或冲太快；
- recover：看它有没有按 desired speed 平滑恢复；
- hold/brake：看它有没有慢下来，并且不要冲过刹车点。

这仍然是干净的底层 tracker reward。它没有 gate reward、aperture reward、obstacle reward、finish reward，也没有 race progress。PPO 不是在学“如何过 Level3 门”，而是在学“给我一小段 reference，我能稳稳照着飞”。

已经验证：

- focused tests：`40 passed, 1 warning`;
- ruff check/format：通过；
- tiny trainer smoke：通过；
- smoke checkpoint 显示 v60 仍是 56 维 input，reward model 是 `reference_command_reward`，gate/obstacle 相关系数全是 0。

下一步应该重新跑 bounded v60 smoke。smoke 只看管线是否干净；如果干净，再开 8M 左右的正式 maturation 训练。
