# Phase 1: Foundation & Scoring Core - Requirements

## Overview

Phase 1 建立项目基础设施和核心评分能力。目标是构建一个最小可用的评分系统，能够对需求文本进行评分并做出拦截决策。

## User Stories

### 1. 项目基础设施

**US-1.1: 作为开发者，我需要一个可运行的 FastAPI 应用骨架**
- 能够启动 HTTP 服务
- 能够访问健康检查端点
- 能够通过环境变量配置

**US-1.2: 作为开发者，我需要统一的配置管理**
- 所有配置通过环境变量读取
- 支持 .env 文件
- 配置有类型安全保证

**US-1.3: 作为开发者，我需要标准化的日志系统**
- 结构化日志输出
- 可配置日志级别
- 包含请求追踪信息

### 2. 数据契约定义

**US-2.1: 作为系统，我需要标准化的输入格式**
- 定义 `RequirementPacket` Schema
- 验证输入合法性
- 拒绝不合法的输入

**US-2.2: 作为系统，我需要标准化的输出格式**
- 定义 `TicketScoreReport` Schema
- 包含评分和问题列表
- 包含人类可读的摘要

**US-2.3: 作为系统，我需要工作流状态管理**
- 定义 `AgentState` TypedDict
- 支持状态传递
- 支持错误记录

### 3. 评分规则配置

**US-3.1: 作为管理员，我需要配置化的评分规则**
- 使用 YAML 定义规则
- 支持 FEATURE/BUG 不同场景
- 支持权重配置

**US-3.2: 作为系统，我需要加载和解析规则**
- 读取 YAML 文件
- 验证规则格式
- 缓存规则配置

### 4. Scoring Agent

**US-4.1: 作为系统，我需要调用 LLM 进行评分**
- 支持 OpenAI API
- 支持 Gemini API（可选）
- 处理 API 错误和超时

**US-4.2: 作为系统，我需要根据规则生成评分**
- 根据 rubric 配置生成 Prompt
- 解析 LLM 返回的 JSON
- 验证输出符合 Schema

**US-4.3: 作为系统，我需要识别阻塞性问题**
- 检测缺失的必填字段（如 AC）
- 检测模糊词汇（如"优化体验"）
- 标记为 BLOCKER 或 WARNING

### 5. Hard Gate

**US-5.1: 作为系统，我需要执行硬性拦截逻辑**
- 分数 < 阈值 → REJECT
- 存在 BLOCKER → REJECT
- 否则 → PASS

**US-5.2: 作为系统，我需要记录拦截决策**
- 记录决策原因
- 记录决策时间
- 支持审计追溯

### 6. 测试覆盖

**US-6.1: 作为开发者，我需要验证 Schema 正确性**
- 测试合法输入
- 测试非法输入
- 测试边界值

**US-6.2: 作为开发者，我需要验证 Scoring Agent**
- 测试评分逻辑
- 测试 BLOCKER 识别
- 测试 LLM 调用（可 mock）

**US-6.3: 作为开发者，我需要验证 Hard Gate**
- 测试拦截逻辑
- 测试边界条件
- 测试决策记录

## Acceptance Criteria

### AC-1: 项目可运行
- Given: 项目依赖已安装
- When: 执行 `uvicorn src.reqgate.app.main:app`
- Then: 服务启动成功，监听 8000 端口

### AC-2: 健康检查可用
- Given: 服务已启动
- When: 访问 `GET /health`
- Then: 返回 `{"status": "ok"}` 和 200 状态码

### AC-3: 配置从环境变量读取
- Given: 设置环境变量 `REQGATE_PORT=9000`
- When: 启动服务
- Then: 服务监听 9000 端口

### AC-4: Schema 验证输入
- Given: 输入 `raw_text` 长度 < 10
- When: 创建 `RequirementPacket`
- Then: 抛出 `ValidationError`

### AC-5: 规则文件可加载
- Given: `scoring_rubric.yaml` 存在
- When: 调用规则加载器
- Then: 返回解析后的规则字典

### AC-6: Scoring Agent 返回合法输出
- Given: 输入一个缺少 AC 的需求
- When: 调用 Scoring Agent
- Then: 返回的 `TicketScoreReport` 包含 `MISSING_AC` 的 BLOCKER

### AC-7: Hard Gate 正确拦截
- Given: `total_score = 80`, `blocking_issues = [...]` (非空)
- When: 调用 Hard Gate
- Then: 返回 `REJECT`

### AC-8: Hard Gate 正确放行
- Given: `total_score = 80`, `blocking_issues = []`
- When: 调用 Hard Gate
- Then: 返回 `PASS`

### AC-9: 测试覆盖率达标
- Given: 执行 `pytest --cov`
- When: 运行所有测试
- Then: 核心模块覆盖率 > 80%

### AC-10: 代码质量检查通过
- Given: 执行 `ruff check` 和 `mypy`
- When: 检查所有代码
- Then: 无错误和警告

## Non-Functional Requirements

### NFR-1: 性能
- Scoring Agent 单次调用 < 30s (P95)
- Schema 验证 < 10ms

### NFR-2: 可维护性
- 所有函数有类型注解
- 所有 Schema 有 docstring
- 代码符合 PEP 8

### NFR-3: 可测试性
- 核心逻辑可单元测试
- LLM 调用可 mock
- 配置可注入

### NFR-4: 安全性
- API Key 不硬编码
- 输入验证在 Schema 层
- 错误信息不泄露敏感数据

## Out of Scope (Phase 1 不包含)

- ❌ Structuring Agent
- ❌ LangGraph 工作流
- ❌ FastAPI 业务路由（只有 /health）
- ❌ Jira/n8n 集成
- ❌ 数据库持久化
- ❌ 监控和追踪

## Success Metrics

### Milestone T1: The First Reject

**测试方式**：
1. 准备一个历史被 Tech Review 打回的真实 Ticket（烂样本）
2. 将其转化为 `RequirementPacket`
3. 调用 Scoring Agent
4. 调用 Hard Gate

**成功标准**：
- [ ] Scoring Agent 返回 `total_score < 60`
- [ ] `blocking_issues` 不为空
- [ ] Hard Gate 返回 `REJECT`
- [ ] 能够准确指出打回原因（如"缺少验收标准"）

## Dependencies

### External Dependencies
- Python 3.14
- FastAPI
- Pydantic (含 pydantic-settings)
- OpenAI Python SDK
- PyYAML
- pytest
- ruff
- mypy

### Internal Dependencies
- 无（Phase 1 是基础）

## Risks & Mitigations

### Risk-1: LLM 评分不准确
- **影响**: 误判率高，PM 不信任系统
- **缓解**: 建立小规模测试集（10 个样本），快速迭代 Prompt
- **应对**: 如果准确率 < 70%，调整 Prompt 或增加 Few-Shot 示例

### Risk-2: LLM API 超时
- **影响**: 用户等待时间过长
- **缓解**: 设置 30s 超时，超时后重试 1 次
- **应对**: 如果频繁超时，考虑切换到更快的模型（如 GPT-3.5）

### Risk-3: Schema 设计不合理
- **影响**: 后续 Phase 需要大量重构
- **缓解**: 参考项目文档中的 Schema 设计，进行充分 review
- **应对**: 预留 Schema 版本化机制

## References

- requirements/项目需求文档.md
- requirements/Agent-2.md (数据契约定义)
- requirements/核心 Prompts 与规则集配置-4.md
- requirements/技术方案.md
