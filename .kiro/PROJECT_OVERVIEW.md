# ReqGate Project Overview

## 项目简介

**ReqGate (Requirement Quality Gate)** 是一个基于 AI 的需求质量门禁系统，通过 LangGraph 工作流和 LLM 自动评估产品需求文档（PRD）的质量，在进入技术评审前拦截低质量需求。

## 核心价值

1. **质量前置**：在 Tech Review 前自动检查需求完整性
2. **自动化反馈**：为 PM 提供即时、具体的修改建议
3. **降本增效**：减少评审会上的无效沟通，提升一次通过率

## 技术栈

- **语言**: Python 3.14
- **框架**: FastAPI + LangGraph
- **Schema**: Pydantic (含 pydantic-settings)
- **LLM**: OpenAI GPT-4o / Google Gemini
- **测试**: pytest
- **质量工具**: ruff (lint/format), mypy (type check)
- **包管理**: uv (优先) / poetry (备选)

## 架构概览

### 三层分离架构

```
┌─────────────────────────────────────────┐
│  L1: Integration Layer (n8n/Jira)      │  ← Phase 3
├─────────────────────────────────────────┤
│  L2: Core Service (FastAPI + LangGraph)│  ← Phase 1-2
├─────────────────────────────────────────┤
│  L3: Infrastructure (Postgres + LLM)   │  ← Phase 1, 4
└─────────────────────────────────────────┘
```

### 核心工作流 (DAG)

```
Input → Guardrail → Structuring → Scoring → Hard Gate → Output
```

## 开发方法论

### Spec-Driven Development

**所有功能必须先创建 Spec，后编写代码。**

#### Spec 结构
```
.kiro/specs/{feature-name}/
├── requirements.md    # 需求定义
├── design.md         # 设计文档
└── tasks.md          # 任务清单
```

#### 开发流程
```
1. Create Spec → 2. Review Spec → 3. Execute Tasks → 4. Verify Milestone
```

## 项目分阶段

### Phase 1: Foundation & Scoring Core (Week 1)
**目标**: 构建最小可用的评分系统

**交付物**:
- 项目骨架 (FastAPI + Pydantic)
- 核心 Schema (RequirementPacket, TicketScoreReport)
- 评分规则配置 (scoring_rubric.yaml)
- Scoring Agent (LLM 评分)
- Hard Gate (拦截逻辑)

**Milestone T1**: 输入烂需求 → 返回评分报告 → 正确拦截

**状态**: 🟡 In Progress

---

### Phase 2: Structuring & Workflow (Week 2)
**目标**: 添加结构化能力和完整工作流

**交付物**:
- PRD_Draft Schema
- Structuring Agent (非结构化 → 结构化)
- Input Guardrail (输入验证)
- LangGraph DAG (完整工作流)
- 容错机制 (降级、重试)

**Milestone T2**: 输入会议纪要 → 生成结构化 PRD → 评分 → 拦截

**状态**: 🔴 Not Started

---

### Phase 3: API & Integration (Week 3)
**目标**: 封装 HTTP API 并集成 Jira/n8n

**交付物**:
- FastAPI 路由 (POST /v1/workflow/run)
- Output Formatter (JSON → Markdown)
- n8n 集成方案
- Jira 适配器 (评论回写)

**Milestone T3**: Jira 创建 Ticket → 自动检查 → 30s 内回复

**状态**: 🔴 Not Started

---

### Phase 4: Operations & Optimization (Week 4+)
**目标**: 建立生产级运维能力

**交付物**:
- PostgreSQL 持久化
- 监控与追踪 (LangSmith/OpenTelemetry)
- 黄金测试集 (40 个样本)
- 反馈闭环 (误判修正)
- 性能优化

**Milestone T4**: 连续运行 3 天，处理 50+ 需求，误判率 < 10%

**状态**: 🔴 Not Started

---

## 目录结构

```
reqgate/
├── .kiro/
│   ├── specs/                          # Spec 文件
│   │   └── phase-1-foundation-scoring/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   ├── steering/                       # IDE 规则
│   │   ├── development-workflow.md
│   │   ├── schema-driven-rules.md
│   │   └── phase-execution-guide.md
│   └── PROJECT_OVERVIEW.md            # 本文件
├── src/reqgate/
│   ├── app/
│   │   └── main.py                    # FastAPI 应用
│   ├── api/
│   │   └── routes.py                  # API 路由
│   ├── config/
│   │   └── settings.py                # 配置管理
│   ├── schemas/
│   │   ├── inputs.py                  # 输入 Schema
│   │   ├── outputs.py                 # 输出 Schema
│   │   └── internal.py                # 内部 Schema
│   ├── agents/
│   │   ├── scoring.py                 # 评分 Agent
│   │   └── structuring.py             # 结构化 Agent (Phase 2)
│   ├── gates/
│   │   ├── rules.py                   # 规则加载器
│   │   └── decision.py                # 门禁决策
│   ├── workflow/
│   │   └── graph.py                   # LangGraph 工作流 (Phase 2)
│   ├── adapters/
│   │   └── llm.py                     # LLM 适配器
│   └── observability/
│       └── logging.py                 # 日志配置
├── tests/
│   ├── test_schemas.py
│   ├── test_scoring_agent.py
│   ├── test_hard_gate.py
│   └── test_integration.py
├── config/
│   └── scoring_rubric.yaml            # 评分规则
├── docs/
│   ├── architecture.md
│   ├── workflow.md
│   └── decisions.md
├── .env.example                       # 环境变量模板
├── .gitignore
├── .cursorrules                       # Cursor IDE 规则
├── pyproject.toml                     # 项目配置
├── README.md
└── Dockerfile                         # 容器化 (Phase 3+)
```

## 核心概念

### Schema-Driven

**Schema 就是法律。所有数据交互必须通过 Pydantic Schema。**

#### 数据契约层级

1. **Input Layer**: `RequirementPacket` - 标准化外部输入
2. **Intermediate Layer**: `PRD_Draft` - 结构化中间态
3. **Output Layer**: `TicketScoreReport` - 最终评分报告
4. **State Layer**: `AgentState` - LangGraph 状态总线

### 评分规则 (Rubric)

使用 YAML 配置化管理评分规则，支持不同场景：

- **FEATURE**: 侧重 AC、User Story、逻辑闭环
- **BUG**: 侧重复现步骤、环境信息

### 硬性门禁 (Hard Gate)

**不依赖 LLM 的确定性逻辑**：

```python
if blocking_issues > 0 or total_score < threshold:
    return REJECT
else:
    return PASS
```

## 开发规范

### 代码风格

- **类型安全**: 所有函数必须有类型注解
- **Schema 优先**: 禁止使用 dict 传递数据
- **配置外部化**: 所有配置通过环境变量
- **错误处理**: 显式处理所有异常

### 测试要求

- **覆盖率**: 核心模块 > 80%
- **单元测试**: 测试单个函数/类
- **集成测试**: 测试组件交互
- **E2E 测试**: 测试完整流程

### Git 规范

```
<type>(<scope>): <subject>

feat(scoring-agent): implement rubric-based scoring
fix(schema): add missing validation
test(hard-gate): add boundary tests
```

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
uv pip install -r requirements.txt

# 或使用 poetry
poetry install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

### 3. 启动服务

```bash
uvicorn src.reqgate.app.main:app --reload --port 8000
```

### 4. 运行测试

```bash
pytest tests/ -v
```

### 5. 代码质量检查

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

## 当前任务

### Phase 1 进度

查看任务清单：`.kiro/specs/phase-1-foundation-scoring/tasks.md`

**下一步**:
1. 如果刚开始 → 执行 Task 1.1 (项目初始化)
2. 如果已初始化 → 按顺序执行后续任务
3. 完成所有任务 → 验证 Milestone T1

## 跨 IDE 协作

### Kiro (Antigravity)
- Spec 创建和规划
- 复杂重构
- 多文件协同修改
- 工作流编排

### Cursor
- 快速代码编写
- 单文件修改
- 调试和问题修复
- 代码补全

### 协作约定
1. 共享 `.kiro/specs/` 中的 Spec
2. 使用相同的 `.env.example` 和 `pyproject.toml`
3. 修改 `tasks.md` 后及时同步
4. 不同 IDE 处理不同的 Phase/Feature

## 重要文件

### 必读文档
- `.kiro/steering/development-workflow.md` - 开发流程规范
- `.kiro/steering/schema-driven-rules.md` - Schema 开发规则
- `.kiro/steering/phase-execution-guide.md` - 分阶段执行指南
- `.cursorrules` - Cursor IDE 规则

### 参考文档
- `requirements/项目需求文档.md` - 系统 PRD
- `requirements/蓝图-1.md` - 宏观架构
- `requirements/Agent-2.md` - 微观实施
- `requirements/Roadmap-3.md` - 实施路线图
- `requirements/核心 Prompts 与规则集配置-4.md` - Prompt 设计
- `requirements/技术方案.md` - 技术执行方案
- `requirements/init_info.md` - 初始化信息

## 常见问题

### Q: 如何创建新的 Spec？
A: 使用命令 "Create a spec for {feature-name}"

### Q: 如何执行 Spec 任务？
A: 使用命令 "Execute task X.X from {spec-name}" 或 "Run all tasks for {spec-name}"

### Q: 如何判断 Phase 是否完成？
A: 检查 tasks.md 中所有 REQUIRED 任务是否为 `[x]`，并验证 Milestone

### Q: 遇到问题怎么办？
A: 查看 `.kiro/steering/development-workflow.md` 的问题升级机制

### Q: 如何切换到下一个 Phase？
A: 完成当前 Phase 的所有任务和 Milestone 验收后，创建下一个 Phase 的 Spec

## 联系与支持

- **Spec 位置**: `.kiro/specs/`
- **规则文件**: `.kiro/steering/`
- **IDE 规则**: `.cursorrules`

---

**记住：Spec First, Code Second. Schema is Law. Quality over Speed.**

Last Updated: 2025-01-21
Current Phase: Phase 1 (Foundation & Scoring Core)
Status: 🟡 In Progress
