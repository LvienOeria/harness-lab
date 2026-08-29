# ADR-002：评估体系设计 —— deterministic-first，capability 与 regression 分离

- 状态：草案，待 review
- 日期：2026-08-30

## 背景

Agent 输出不确定、轨迹长、成本波动大。评估体系决定整个项目的可信度。

## 决策

1. **确定性判定优先**：v0 的 24 个任务至少 80% 使用文件树 diff、输出 schema、数值断言、pytest、工具调用序列等确定性 grader。
2. **DeepSeek judge 只用于主观题**：固定 `deepseek-v4-pro`、temperature=0、固定 rubric；judge 分数与规则分数分列报告，并对 ≥10% 样本做人工抽检。
3. **capability 与 regression 分离**：capability suite 用于比较配置优劣（期待有区分度）；regression suite 应接近 100%，用于发现 harness 集成事故。
4. **报告 model × harness 配置，而非单一总分**：沿用 Harness-Bench 的方法论；每个配置独立报告 completion、pass@k（k=1,3）、tokens、cost、steps、wall time。
5. **失败分类自动化**：tool misuse / schema error / context loss / incomplete artifact / execution misalignment 五类，分类器先用规则，不引入额外模型。
6. **成本模型**：按 DeepSeek 官方定价分别计算 flash/pro 的 input/output token 费用；缓存命中不计输入费用（如 API 返回 usage 支持）。

## 任务设计规则

每个任务必须满足：

- **offline**：不访问外网，不读取仓库外路径。
- **oracle-checkable**：存在确定性 grader，且人工确认 grader 不是靠运气通过。
- **solvable**：至少由作者用 baseline 或 dsh 跑通过一次，并保留证据。
- **bounded**：单任务预算（tokens/步数/时间）写在 `task.json`，超预算判失败。
- **fresh-workspace**：每次运行从 fixture 复制干净 workspace，防止状态泄漏。

## 非确定性的处理

- 确定性任务：每配置默认跑 3 次，报告 pass@1 和 pass@k，方差写入报告。
- 若 DeepSeek API 出现短时限流，重试退避后仍失败的任务标记为 `infra_failure`，不计入 completion 分子，但单独披露。

## 禁止事项

- 禁止用训练集答案微调 grader 阈值。
- 禁止只展示「最优配置」的挑选后结果；必须公开全矩阵原始 JSONL/CSV。
