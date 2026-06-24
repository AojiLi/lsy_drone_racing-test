# Level3 Loop Notes

这个目录放每一轮 Level3 loop 的通俗笔记。

目的不是替代 `experiments/level3_ppo_loop/state.json`、analysis packet 或
decision packet，而是给人看的快速回顾：

- 这轮到底试了什么；
- 为什么要这么试；
- 结果是多少；
- 为什么没有或已经解决 Level3；
- 下一轮准备怎么改；
- 哪些东西明确没有改，比如 `config/level3.toml` 赛道。

每轮训练、评估、analyzer、三个决策 review 和 main-agent decision 完成后，
再额外生成一份 reader note。默认文件名格式：

```text
loopNNN-<proposal>.md
```

辅助脚本：

```bash
pixi run -e gpu python scripts/write_level3_loop_reader_note.py --update-state
```

如果 reader-note 子 agent 额外写了一段更通俗的总结，可以放到临时文本文件，
再用：

```bash
pixi run -e gpu python scripts/write_level3_loop_reader_note.py \
  --reader-summary-file /path/to/summary.txt \
  --update-state
```
