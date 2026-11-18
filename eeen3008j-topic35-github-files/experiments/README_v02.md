# v0.2 正式复现

当前方法：experiment_spec_v02.md；结果：results_summary_v02.md；代码Python3.10+。v0.1保留在原文件及results/v0.1_smoke，不要再次生成build_v02.py覆盖已冻结实现。

从工作区根目录运行：

```powershell
python -m pip install --target experiments/.deps -r experiments/requirements_analysis.txt
python -X utf8 -m unittest discover -s experiments -v
python -X utf8 experiments/scan_v02.py --benchmark
python -X utf8 experiments/scan_v02.py --workers 4
python -X utf8 experiments/analyze_results.py
python -X utf8 experiments/supplement.py
python -X utf8 experiments/plot_results.py
python -X utf8 experiments/audit_release.py
```

本机依赖已安装在experiments/.deps。模拟/扫描仅需标准库；分析/图表用requirements固定依赖。`-X utf8`避免Windows默认GBK读含中文配置时出错。

扫描按480批次缓存，重运行同源码时复用缓存重组CSV；源码/配置哈希改变会拒绝混跑。完整从零重跑可将整个experiments文件夹（不含results与.deps）复制到新的工作目录后运行上述命令，输出始终相对于脚本目录，不删除或覆盖本轮基准集。字节CSV/指标应确定性一致；elapsed计时允许不同。不要修改冻结源码再复用旧批次。

统计可重跑，selected_configs仅用tuning_runs选择并先保存；然后读取evaluation_runs，输出每点与配对bootstrap。bootstrap不是逐时间点抽样，未做同时区间/多重比较调整。补充和绘图只在本角色目录写文件。

manifest.json记录扫描源码、完整配置和主CSV哈希；statistics_manifest记录分析版本；release_audit记录实际发布产物哈希与守恒检查。validation_v02.txt保存18项通过的测试记录。分阶段空failures.log表示本次正式阶段无失败。最初依赖下载失败是环境设置问题，未算作正式扫描运行失败。

3幅主图各有PDF/SVG/PNG，优先报告嵌入PDF/SVG。PNG已视觉检查；未进行独立PDF渲染或自动色觉模拟。不得把本简化模型的结果称为真实网络验证。
