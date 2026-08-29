# ADR-001：评测基座选择 —— 基于 DeepSeek Harness，而不是自研完整 harness

- 状态：草案，待 review
- 日期：2026-08-30
- 决策者：项目负责人

## 背景

harness-lab 需要评测 agent loop、compaction、skill、工具集等配置。评测基座有四种选项：

1. **完全自研 harness**：从 message loop、工具协议、上下文管理全部自己写。
2. **DeepSeek Harness（dsh）**：官方 developer preview，MIT，插件化，已有 skills/compaction/session 等子系统。
3. **LangGraph 等通用编排框架**：成熟但与 DeepSeek 平台叙事弱绑定，且封装层次较高。
4. **直接用 Anthropic Agent SDK 等第三方 harness**：需要非 DeepSeek 生态依赖，与硬约束冲突。

## 决策

**采用 DeepSeek Harness（锁定版本）作为生产级评测基座，同时在仓库内实现一个最小 ReAct baseline 作为可解释对照。**

理由：

1. 本项目面向「大模型厂商 / Agent 平台产品」岗位，核心叙事是：**会使用、评测、改进真实生产级 harness**，而不是再造一个 toy harness。
2. dsh 是 DeepSeek 官方生态当前最值得研究的 agent 基础设施，且源码公开、MIT、插件化；评测它本身就是有产品价值的选题。
3. dsh 已内置 compaction、skill、session 持久化等子系统，正好覆盖本项目要消融的配置。
4. 自写 ReAct baseline 不是为了替代 dsh，而是提供最小可解释对照：让 benchmark 能区分「harness 的贡献」与「模型的贡献」。

## 后果

### 正面

- 项目具有平台级技术深度和时效性。
- 评测结论对 DeepSeek Harness 用户有直接参考价值。
- 代码量可控：核心工作聚焦任务、grader、配置矩阵，而非重写基础设施。

### 负面与对策

- dsh 是 developer preview，接口可能破坏性变更。
  - 对策：锁版本；所有 dsh 调用收敛到 `runners/dsh_runner.py` 适配层；baseline-react 保证仓库在 dsh 不可用时仍能完整运行。
- 某些高级能力（插件开发）可能是 TypeScript 生态，增加栈复杂度。
  - 对策：v0 只用 Python SDK 能稳定的能力；TS 插件推迟到 v1.1，除非 Python 路径完全不可行。

## 约束

- 只使用 DeepSeek API，不引入其他云端 LLM。
- 不依赖 Docker。
- 所有结论必须同时报告 dsh 与 baseline 的运行结果，禁止只报单边。
