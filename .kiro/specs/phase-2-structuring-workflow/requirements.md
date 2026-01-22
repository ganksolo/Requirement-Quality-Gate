# Phase 2: Structuring & Workflow Pipeline - Requirements

## Overview

Phase 2 在 Phase 1 的基础上，添加结构化能力和完整的工作流管线。目标是将非结构化的需求输入（会议纪要、草稿）转化为标准化的 PRD，并通过 LangGraph 串联完整的处理流程。

## User Stories

### 1. PRD 结构化能力

**US-1.1: 作为 PM，我需要系统帮我整理杂乱的需求文本**
- 输入会议录音转录或草稿
- 自动提取 User Story、AC、Edge Cases
- 生成结构化的 PRD 草稿

**US-1.2: 作为 PM，我需要系统告诉我缺少了什么信息**
- 系统识别缺失的关键字段
- 生成针对性的澄清问题
- 引导我补充必要信息

**US-1.3: 作为系统，我需要防止 AI 编造信息**
- 只提取原文中存在的信息
- 对不确定的内容标记为 missing
- 严禁幻觉（Hallucination）

### 2. 输入防护

**US-2.1: 作为系统，我需要拦截不合规的输入**
- 检测输入长度（过短或过长）
- 识别敏感信息（PII）
- 防止 Prompt 注入攻击

**US-2.2: 作为系统，我需要对输入进行预处理**
- 清洗无关噪音
- 标准化格式
- 截断或分块处理超长文本

### 3. 工作流编排

**US-3.1: 作为系统，我需要串联所有处理节点**
- 使用 LangGraph 定义 DAG
- 管理节点间的状态传递
- 支持条件分支

**US-3.2: 作为系统，我需要处理节点失败**
- Structuring 失败时降级到直接评分
- LLM 超时时重试
- 记录错误日志

**US-3.3: 作为系统，我需要追踪工作流执行**
- 记录每个节点的输入输出
- 追踪状态变化
- 支持调试和审计

### 4. 容错与降级

**US-4.1: 作为系统，我需要在 Structuring 失败时继续运行**
- 检测 Structuring Agent 失败
- 降级到 Raw Mode（直接评分原始文本）
- 扣除"结构化失败"的分数

**US-4.2: 作为系统，我需要处理 LLM 超时**
- 设置合理的超时时间
- 超时后重试（最多 N 次）
- 重试失败后返回友好错误

**US-4.3: 作为系统，我需要防止循环打回**
- 检测连续打回次数
- 超过阈值时触发人工介入
- 通知 Tech Lead 处理

## Acceptance Criteria

### AC-1: PRD 结构化成功
- Given: 输入一段 300 字的会议纪要
- When: 调用 Structuring Agent
- Then: 返回包含 User Story 和至少 1 条 AC 的 `PRD_Draft`

### AC-2: 缺失信息识别
- Given: 输入的需求缺少验收标准
- When: 调用 Structuring Agent
- Then: `missing_info` 包含 "acceptance_criteria"，`clarification_questions` 不为空

### AC-3: 幻觉防护
- Given: 输入的需求未提及异常流程
- When: 调用 Structuring Agent
- Then: `edge_cases` 为空或 null，不包含编造的内容

### AC-4: 输入长度检查
- Given: 输入文本长度 < 10 字符
- When: 通过 Input Guardrail
- Then: 直接拒绝，返回错误信息

### AC-5: PII 过滤
- Given: 输入包含手机号或邮箱
- When: 通过 Input Guardrail
- Then: 敏感信息被脱敏或标记

### AC-6: Prompt 注入防护
- Given: 输入包含 "Ignore all previous instructions"
- When: 通过 Input Guardrail
- Then: 识别为��击，拒绝处理

### AC-7: 完整工作流执行
- Given: 输入一个合法的 RequirementPacket
- When: 执行完整 LangGraph 工作流
- Then: 依次通过 Input Guardrail → Structuring → Scoring → Hard Gate

### AC-8: Structuring 失败降级
- Given: Structuring Agent 返回错误或超时
- When: 工作流继续执行
- Then: Scoring Agent 直接对 `raw_text` 评分，`total_score` 扣除 10 分

### AC-9: LLM 超时重试
- Given: LLM 调用超时
- When: 触发重试机制
- Then: 最多重试 2 次，失败后返回 503 错误

### AC-10: State Management Correct
- Given: Workflow execution in progress
- When: Inspect AgentState
- Then: Contains all Phase 1 fields (`packet`, `score_report`, `retry_count`, `error_logs`) plus Phase 2 additions (`structured_prd`, `fallback_activated`, `execution_times`)

### AC-11: Phase 1 Backward Compatibility
- Given: All Phase 1 tests from `tasks.md`
- When: Run `pytest tests/` after Phase 2 implementation
- Then: All 82 Phase 1 tests continue to pass

## Non-Functional Requirements

### NFR-1: 性能
- Structuring Agent 单次调用 < 20s (P95)
- 完整工作流端到端 < 60s (P95)
- Input Guardrail 检查 < 100ms

### NFR-2: 可靠性
- Structuring 失败时系统不崩溃
- LLM 超时时自动重试
- 降级模式下仍能产出评分报告

### NFR-3: 可追溯性
- 记录每个节点的执行时间
- 记录状态变化历史
- 记录错误和重试次数

### NFR-4: 安全性
- PII 信息不发送给 LLM
- Prompt 注入攻击被拦截
- 敏感日志不记录原始文本

## Out of Scope (Phase 2 不包含)

- ❌ HTTP API 接口（Phase 3）
- ❌ Jira/n8n 集成（Phase 3）
- ❌ 数据库持久化（Phase 4）
- ❌ 监控面板（Phase 4）
- ❌ 异步回调（Phase 3）

## Success Metrics

### Milestone T2: End-to-End Workflow

**测试方式**：
1. 准备一段 300 字的会议纪要（包含需求但格式混乱）
2. 创建 `RequirementPacket` 并执行完整工作流
3. 观察每个节点的输出

**成功标准**：
- [ ] Structuring Agent 生成了结构化的 `PRD_Draft`
- [ ] `PRD_Draft` 包含 User Story 和至少 1 条 AC
- [ ] Scoring Agent 基于 `PRD_Draft` 进行了评分
- [ ] Hard Gate 做出了正确的决策（Pass/Reject）
- [ ] 整个流程无崩溃，耗时 < 60s

### Milestone T2.1: Degradation Test

**测试方式**：
1. 模拟 Structuring Agent 失败（Mock 返回错误）
2. 执行工作流

**成功标准**：
- [ ] 工作流没有中断
- [ ] Scoring Agent 对原始文本进行了评分
- [ ] `total_score` 被扣除了降级惩罚分
- [ ] 错误被记录到 `error_logs`

## Dependencies

### External Dependencies
- LangGraph (工作流编排)
- Phase 1 的所有依赖

### Internal Dependencies
- **Phase 1 must be complete**: All 82 tests passing
- **Reuse Phase 1 Schemas**: `RequirementPacket`, `TicketScoreReport`, `ReviewIssue` (unchanged)
- **Reuse Phase 1 Config**: `RubricScenarioConfig` in `schemas/config.py` (extend, don't replace)
- **Reuse LLM Adapter**: `LLMClient`, `OpenAIClient` in `adapters/llm.py` (extend with retry logic)
- **Reuse Scoring Agent**: `ScoringAgent` in `agents/scoring.py` (add fallback mode support)
- **Reuse Hard Gate**: `HardGate` in `gates/decision.py` (no changes needed)

## Risks & Mitigations

### Risk-1: Structuring Agent 产生幻觉
- **影响**: 生成的 PRD 包含原文不存在的内容
- **缓解**: 在 Prompt 中强约束"只提取，不编造"
- **应对**: 添加验证逻辑，对比原文和提取结果

### Risk-2: LangGraph 学习曲线
- **影响**: 开发时间延长
- **缓解**: 先实现简单的线性流程，再添加分支
- **应对**: 参考 LangGraph 官方示例

### Risk-3: 工作流性能问题
- **影响**: 端到端耗时超过 60s
- **缓解**: 优化 Prompt 长度，使用更快的模型
- **应对**: 考虑异步处理（Phase 3）

### Risk-4: 降级逻辑复杂
- **影响**: 容错代码难以测试
- **缓解**: 为每种失败场景编写单元测试
- **应对**: 使用 Mock 模拟各种失败情况

## References

- docs/项目需求文档.md
- docs/Agent-2.md (PRD_Draft Schema 定义)
- docs/核心 Prompts 与规则集配置-4.md (Structuring Prompt)
- docs/Roadmap-3.md (Phase 2 规划)
- docs/技术方案.md (LangGraph 架构)
- Phase 1 Spec (基础设施和 Scoring Agent)
