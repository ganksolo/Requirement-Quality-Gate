# ReqGate Spec-Driven Development Guide

## 📋 概述

本项目采用 **Spec-Driven Development** 方法论，所有功能开发必须先创建 Spec，后编写代码。

## 🗂️ Spec 文件结构

```
.kiro/specs/{feature-name}/
├── requirements.md    # 需求定义（User Stories + Acceptance Criteria）
├── design.md         # 设计文档（架构、Schema、API 设计）
└── tasks.md          # 任务清单（可执行的开发任务）
```

## 🎯 当前项目状态

### 已创建的 Spec

#### ✅ Phase 1: Foundation & Scoring Core
- **路径**: `.kiro/specs/phase-1-foundation-scoring/`
- **状态**: 🟡 Ready for Implementation
- **目标**: 构建最小可用的评分系统
- **任务数**: 35 个任务（32 必需 + 3 可选）
- **预计时间**: 1 周

### 待创建的 Spec

#### 🔴 Phase 2: Structuring & Workflow
- **预计创建时间**: Phase 1 完成后
- **目标**: 添加结构化能力和 LangGraph 工作流

#### 🔴 Phase 3: API & Integration
- **预计创建时间**: Phase 2 完成后
- **目标**: 封装 HTTP API 并集成 Jira/n8n

#### 🔴 Phase 4: Operations & Optimization
- **预计创建时间**: Phase 3 完成后
- **目标**: 建立生产级运维能力

## 🚀 如何使用 Spec

### 在 Kiro (Antigravity) 中

#### 1. 查看 Spec
```
"Show me the requirements for phase-1-foundation-scoring"
"Show me the design for phase-1-foundation-scoring"
"Show me the tasks for phase-1-foundation-scoring"
```

#### 2. 执行单个任务
```
"Execute task 1.1.1 from phase-1-foundation-scoring"
```

#### 3. 执行所有任务
```
"Run all tasks for phase-1-foundation-scoring"
```

#### 4. 创建新 Spec
```
"Create a spec for phase-2-structuring-workflow"
```

### 在 Cursor 中

#### 1. 手动查看 Spec
- 打开 `.kiro/specs/phase-1-foundation-scoring/requirements.md`
- 打开 `.kiro/specs/phase-1-foundation-scoring/design.md`
- 打开 `.kiro/specs/phase-1-foundation-scoring/tasks.md`

#### 2. 按照 tasks.md 执行
- 找到未完成的任务（`[ ]`）
- 实现该任务
- 更新任务状态为 `[x]`

#### 3. 遵循 .cursorrules
- Cursor 会自动读取 `.cursorrules` 文件
- 按照规则进行代码编写

## 📝 开发流程

### 标准流程

```
1. 阅读 requirements.md
   ↓
2. 阅读 design.md
   ↓
3. 查看 tasks.md
   ↓
4. 执行任务（一次一个）
   ↓
5. 更新任务状态
   ↓
6. 运行测试
   ↓
7. 验证 Milestone
```

### 任务状态标记

```markdown
- [ ] 未开始 (Not Started)
- [~] 已排队 (Queued)
- [-] 进行中 (In Progress)
- [x] 已完成 (Completed)
- [ ]* 可选任务 (Optional)
```

### 任务执行规则

#### 单任务模式（推荐）
- 一次只执行一个任务
- 完成后停止，等待 review
- 不自动继续下一个任务

#### 批量模式
- 使用 "run all tasks" 命令
- 按顺序执行所有 REQUIRED 任务
- 遇到错误立即停止

## 🎓 Phase 1 快速开始

### Step 1: 理解需求
```bash
# 阅读需求文档
cat .kiro/specs/phase-1-foundation-scoring/requirements.md
```

**关键需求**:
- 构建 FastAPI 应用骨架
- 定义核心 Schema (RequirementPacket, TicketScoreReport)
- 实现 Scoring Agent (LLM 评分)
- 实现 Hard Gate (拦截逻辑)
- 创建评分规则配置 (YAML)

### Step 2: 理解设计
```bash
# 阅读设计文档
cat .kiro/specs/phase-1-foundation-scoring/design.md
```

**关键设计**:
- 分层架构（Application → Configuration → Schema → Business Logic → Infrastructure）
- Schema-Driven（所有数据用 Pydantic）
- 配置化规则（YAML）
- 单例模式（Settings, LLM Client, Rubric Loader）

### Step 3: 查看任务
```bash
# 查看任务清单
cat .kiro/specs/phase-1-foundation-scoring/tasks.md
```

**任务分组**:
1. 项目设置 (1.1-1.3)
2. 配置层 (2.1-2.2)
3. Schema 层 (3.1-3.3)
4. 规则配置 (4.1-4.2)
5. LLM 基础设施 (5.1)
6. Scoring Agent (6.1-6.2)
7. Hard Gate (7.1)
8. 集成测试 (8.1-8.3)
9. Milestone 验证 (9.1)

### Step 4: 开始执行

#### 使用 Kiro
```
"Execute task 1.1.1 from phase-1-foundation-scoring"
```

#### 使用 Cursor
1. 打开 `tasks.md`
2. 找到 Task 1.1.1
3. 按照设计文档实现
4. 标记为 `[x]`

### Step 5: 验证 Milestone

**Milestone T1: The First Reject**

测试步骤：
1. 准备一个烂需求（缺少 AC）
2. 创建 `RequirementPacket`
3. 调用 Scoring Agent
4. 调用 Hard Gate
5. 验证返回 `REJECT`

成功标准：
- [ ] `total_score < 60`
- [ ] `blocking_issues` 包含 `MISSING_AC`
- [ ] Hard Gate 返回 `REJECT`
- [ ] 能准确指出打回原因

## 📚 重要文档

### 必读
1. **开发流程**: `.kiro/steering/development-workflow.md`
2. **Schema 规则**: `.kiro/steering/schema-driven-rules.md`
3. **Phase 指南**: `.kiro/steering/phase-execution-guide.md`
4. **项目概览**: `.kiro/PROJECT_OVERVIEW.md`

### 参考
1. **项目需求**: `docs/项目需求文档.md`
2. **架构蓝图**: `docs/蓝图-1.md`
3. **微观实施**: `docs/Agent-2.md`
4. **实施路线**: `docs/Roadmap-3.md`
5. **Prompt 配置**: `docs/核心 Prompts 与规则集配置-4.md`
6. **技术方案**: `docs/技术方案.md`
7. **初始化信息**: `docs/init_info.md`

## 🔧 开发工具

### 代码质量
```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/
```

### 测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_schemas.py -v

# 测试覆盖率
pytest tests/ --cov=src/reqgate --cov-report=html
```

### 启动服务
```bash
# 开发模式
uvicorn src.reqgate.app.main:app --reload --port 8000

# 访问健康检查
curl http://localhost:8000/health
```

## ⚠️ 注意事项

### 必须遵守的规则

1. **Spec First**: 先有 Spec，后有代码
2. **Schema-Driven**: 所有数据用 Pydantic，禁止 dict
3. **Type Safety**: 所有函数必须有类型注解
4. **No Hardcode**: 配置通过环境变量，不硬编码
5. **Test Everything**: 核心逻辑必须有测试

### 禁止的做法

❌ 跳过 Spec 直接写代码
❌ 使用 dict 传递数据
❌ 函数没有类型注解
❌ 硬编码 API Key
❌ 不写测试

## 🤝 跨 IDE 协作

### Kiro 适合
- 创建和规划 Spec
- 执行复杂的多文件任务
- 重构和架构调整
- 批量执行任务

### Cursor 适合
- 快速编写单个文件
- 调试和修复问题
- 代码补全和优化
- 单任务执行

### 协作建议
1. 使用 Kiro 创建 Spec
2. 使用 Cursor 快速实现
3. 使用 Kiro 执行集成测试
4. 两个 IDE 共享相同的 Spec 和配置

## 📞 获取帮助

### 遇到问题时

1. **查看文档**: 先查看 `.kiro/steering/` 中的规则文档
2. **查看 Spec**: 确认 requirements.md 和 design.md
3. **查看示例**: 参考项目文档中的代码示例
4. **询问 AI**: 在 Kiro 或 Cursor 中询问具体问题

### 问题升级

遇到以下情况立即停止并报告：
- 连续 3 次测试失败
- Spec 与实现严重不符
- 发现架构级问题
- 依赖冲突无法解决

## 🎉 下一步

### 如果你是第一次使用

1. 阅读 `.kiro/PROJECT_OVERVIEW.md`
2. 阅读 `.kiro/steering/development-workflow.md`
3. 查看 Phase 1 的 requirements.md
4. 开始执行 Task 1.1.1

### 如果 Phase 1 已完成

1. 验证 Milestone T1
2. 创建 Phase 2 Spec
3. Review Phase 1 经验教训
4. 开始 Phase 2 开发

---

**记住：Spec First, Code Second. 质量优于速度。**

Happy Coding! 🚀
