# harness-lab PRD（v0.1 draft，待 review）

> 一句话：在 DeepSeek Harness 之上，做一个可复现、可视化的 agent harness 配置评测台。
> English: An evaluation harness for DeepSeek Harness that benchmarks agent loops, compaction, skills, and tool configurations on reproducible offline tasks.
> 状态：草案，尚未开始编码。

## 1. 背景与问题

2026 年 Agent 平台的关键事实：同一个模型，换一套 harness 配置（loop、compaction、skill、工具集、权限策略），完成率与成本可能发生数量级变化。Harness-Bench（arXiv:2605.27922）在 5,194 条轨迹上证明：**能力应当报告为 model × harness 配置，而不是只报告模型**。DeepSeek 官方 Harness 已进入 developer preview，插件化、含 skills/compaction 子系统，但缺少面向选型者的产品化评测层。

本仓库要回答的问题：

- 什么任务应该用 plan-execute 而不是 ReAct？
- 1M 上下文下，compaction 还值不值得开？
- 注入 Skill 对完成率和 token 成本的实际影响是多少？
- `deepseek-v4-flash` + 好 harness 能否追平 `deepseek-v4-pro` + 朴素 harness？

## 2. 目标用户

1. **Agent 平台产品经理**：需要数据支持 harness 默认配置与用户引导。
2. **AI 应用团队**：需要决定 loop、工具集、上下文策略。
3. **模型厂商/开发者关系**：需要展示模型在真实 harness 下的行为，而不是裸 benchmark。

## 3. 目标 / 非目标

### 目标（v1）

- 提供 24 个以上**离线、可复现、可判定**的 agent 任务。
- 支持 DeepSeek Harness（锁版本）与自写最小 ReAct 基线的对照运行。
- 支持至少 4 类 harness 配置消融：loop pattern、compaction、skill、tool set。
- 输出 completion、pass@k、token、成本、步数、execution-alignment failures。
- 提供 trace viewer 和「Harness 配置决策手册」报告。

### 非目标（v1）

- 不训练模型、不微调。
- 不接入 Docker/K8s 多租户调度；沙盒用隔离临时目录 + subprocess。
- 不自研第二个生产级 agent harness；自写 ReAct 仅作为可解释基线。
- 不评测 GUI/浏览器 agent（留给未来扩展）。

## 4. 成功指标（v1 验收）

| 指标 | 目标 |
|---|---|
| 任务数 | ≥ 24，覆盖 5 个 suite |
| 复现性 | 同一 commit 连续 3 次运行，确定性任务完成率方差 ≤ 2pp |
| 配置矩阵 | 至少 8 组 model × harness 配置跑通并出报告 |
| 指标完整性 | 每配置输出 completion、tokens、cost、steps、时延、失败分类 |
| Demo | 一个 GIF：从 `uv run harness-lab run ...` 到 dashboard 图表 |
| 文档 | PRD、ADR、BENCHMARK.md、README 完整 |

## 5. 功能需求

### 5.1 任务套件（v0 建议 24 个）

| Suite | 任务示例 | 判定方式 |
|---|---|---|
| `file-ops` | 按规则整理混装目录、批量重命名、提取指定字段 | 文件树 diff / 文件内容断言 |
| `data-clean` | 去重 CSV、修复缺失值、生成汇总 JSON | 输出 schema + 数值断言 |
| `mini-code` | 修复 2–5 个函数的 bug，通过 pytest | fail-to-pass / pass-to-pass |
| `long-qa` | 从 20–50 页给定文档回答事实问题并引用章节 | 答案包含/精确匹配 + 引用定位 |
| `tool-route` | 按正确顺序调用注册工具，处理缺参/错误分支 | 工具调用序列断言 |

任务全部使用**仓库内 fixtures**，不访问外网；每个任务有 `task.json`、`workspace/`、`grader.py`、`solution.md`（供人工校验可达性）。

### 5.2 Harness 配置矩阵

- 模型：`deepseek-v4-flash`（thinking on/off）、`deepseek-v4-pro`（thinking on）。
- 执行器：`dsh`（Python SDK，锁版本）与 `baseline-react`（自研最小循环）。
- loop/pattern：baseline ReAct；dsh 默认；plan-first；reflection-on-error；router（简单工具 vs 代码执行）。
- 上下文：compaction off / auto；note file off / on；skill off / 1 个最小 skill pack。
- 工具集：lean（仅必需）vs full（全部注册）——用于验证 Anthropic「工具集最小化」建议。

### 5.3 评估系统

- deterministic checker 优先；DeepSeek judge 仅用于主观题，并固定 judge 模型与温度。
- capability tasks（当前通过率较低）与 regression tasks（应接近 100%）分开报告。
- 每条轨迹记录：messages、tool calls、workspace diff、tokens、cost、步数、wall time。
- 失败自动分类：tool misuse、schema error、context loss、incomplete artifact、execution misalignment。

### 5.4 Dashboard 与报告

- Streamlit dashboard：任务 × 配置热力图、token/cost 散点、轨迹回放。
- 自动生成 `BENCHMARK.md`：日期、模型版本、任务数、通过率、成本表、复现命令。
- `docs/playbook.md`：从实验结果归纳的 harness 配置决策建议。

## 6. 技术架构（v0）

- Python 3.13 + `uv`；DeepSeek API 走 OpenAI-compatible client。
- `deepseek-harness-sdk` 锁版本；若 preview 接口变更，所有 dsh 调用收敛在 `harnesslab/runners/dsh_runner.py` 一个适配层。
- 沙盒：`tempfile` + 受限工作目录 + `subprocess(timeout=...)`；不依赖 Docker。
- 结果存储：SQLite + JSONL traces；可视化用 Streamlit + Plotly。
- 成本计算：按 DeepSeek 官方 input/output 定价（flash/pro 分开），只统计模型 token。

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| DeepSeek Harness preview 破坏性变更 | 锁版本；适配层隔离；baseline-react 始终可跑，保证仓库不会整体失效 |
| DeepSeek judge 与 agent 同模型偏差 | 只用规则判定核心分数；judge 分数单独列示并做 10% 人工抽检 |
| 任务可解性不足 | 每个任务先人工跑通 baseline；不可解任务移出 capability 套件 |
| subprocess 安全 | 只跑仓库内测试脚本；设置超时、输出上限、禁外网模式 |
| API 并发/限流 | 串行优先 + 可配置并发 + 自动重试与退避 |

## 8. 里程碑

- M0（当前）：PRD/ADR review。
- M1：repo 初始化、fixtures 规范、3 个任务、baseline-react 跑通。
- M2：dsh runner 适配、12 个任务、SQLite/trace 落地。
- M3：24 个任务、完整配置矩阵、失败分类。
- M4：dashboard、BENCHMARK.md、demo GIF、README/PRD 定稿、发布。

## 9. 仓库结构（草案）

```text
harness-lab/
  README.md
  LICENSE
  pyproject.toml
  docs/PRD.md docs/ADR/ docs/BENCHMARK.md
  src/harnesslab/
    api/            # DeepSeek client 封装
    tasks/          # task loader + fixtures
    runners/        # dsh_runner, react_runner
    graders/        # checker, llm_judge
    metrics/        # tokens/cost/steps
    ui/             # Streamlit dashboard
  tasks/            # 24 个任务的 fixtures 与 grader
  experiments/      # 配置矩阵定义与运行结果
  tests/
  .github/workflows/ci.yml   # 默认 offline fixtures，不需要 API key
```

## 10. Definition of Done（v1）

- [ ] 24 个任务全部有 oracle 可达证据。
- [ ] ≥ 8 组配置跑通，`BENCHMARK.md` 数据可复现。
- [ ] 单条命令可复现任一配置：`uv run harness-lab run --config experiments/xxx.yaml`。
- [ ] README 首屏满足简历解析约定。
- [ ] 不依赖本作品集任何其他仓库。
