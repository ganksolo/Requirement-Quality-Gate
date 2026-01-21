# 🚀 START HERE - ReqGate Project Guide

> **这是 ReqGate 项目的入口文档。如果你是第一次接触这个项目，请从这里开始。**

---

## 📌 快速定位

### 我是谁？我应该读什么？

#### 🤖 如果你是 AI Assistant (Kiro/Cursor)
**立即阅读**：
1. 本文件（了解项目背景）
2. `.kiro/PROJECT_OVERVIEW.md`（项目全貌）
3. `SPEC_GUIDE.md`（如何使用 Spec）
4. `.kiro/steering/development-workflow.md`（开发规范）

**当前任务**：
- 查看 `.kiro/specs/phase-1-foundation-scoring/tasks.md`
- 执行未完成的任务

#### 👨‍💻 如果你是开发者
**立即阅读**：
1. 本文件（了解项目背景）
2. `README.md`（项目说明和快速开始）
3. `SPEC_GUIDE.md`（Spec 使用指南）
4. `.kiro/specs/phase-1-foundation-scoring/requirements.md`（当前需求）

---

## 🎯 项目是什么？

**ReqGate (Requirement Quality Gate)** = 需求质量门禁系统

### 一句话概括
用 AI 自动检查产品需求文档（PRD）的质量，在技术评审前拦截低质量需求。

### 核心功能
```
输入：PM 写的需求文档（可能很烂）
  ↓
处理：AI 评分 + 规则检查
  ↓
输出：
  - ✅ PASS：需求质量合格，可以进入技术评审
  - ❌ REJECT：需求质量不合格，返回具体的修改建议
```

### 技术栈
- **Python 3.14** + **FastAPI** + **LangGraph**
- **Pydantic** (Schema-Driven)
- **OpenAI GPT-4o** / **Google Gemini**
- **pytest** + **ruff** + **mypy**

---

## 📚 核心文档索引

### 🔴 必读文档（按顺序）

| 序号 | 文档 | 用途 | 阅读时间 |
|------|------|------|----------|
| 1 | `START_HERE.md` | 项目入口（本文件） | 5 分钟 |
| 2 | `.kiro/PROJECT_OVERVIEW.md` | 项目全貌和架构 | 15 分钟 |
| 3 | `SPEC_GUIDE.md` | Spec 使用指南 | 10 分钟 |
| 4 | `.kiro/steering/development-workflow.md` | 开发流程规范 | 15 分钟 |

### 🟡 重要文档（需要时查阅）

| 文档 | 用途 |
|------|------|
| `.kiro/steering/schema-driven-rules.md` | Schema 开发详细规则 |
| `.kiro/steering/phase-execution-guide.md` | 分阶段执行指南 |
| `.cursorrules` | Cursor IDE 专用规则 |
| `.kiro/SETUP_COMPLETE.md` | 项目设置完成总结 |

### 🟢 参考文档（深入了解）

| 文档 | 用途 |
|------|------|
| `docs/项目需求文档.md` | 系统 PRD（产品需求） |
| `docs/蓝图-1.md` | 宏观架构设计 |
| `docs/Agent-2.md` | 微观实施细节 |
| `docs/Roadmap-3.md` | 实施路线图 |
| `docs/核心 Prompts 与规则集配置-4.md` | Prompt 设计 |
| `docs/技术方案.md` | 技术执行方案 |
| `docs/init_info.md` | 初始化信息 |

---

## 🏗️ 项目当前状态

### Phase 1: Foundation & Scoring Core
**状态**: 🟡 Spec 已创建，待实施

**目标**: 构建最小可用的评分系统

**Spec 位置**: `.kiro/specs/phase-1-foundation-scoring/`
- `requirements.md` - 需求定义
- `design.md` - 设计文档
- `tasks.md` - 任务清单（35 个任务）

**Milestone T1**: 输入烂需求 → 返回评分报告 → 正确拦截

### 后续 Phase
- **Phase 2**: Structuring & Workflow（待创建）
- **Phase 3**: API & Integration（待创建）
- **Phase 4**: Operations & Optimization（待创建）

---

## 🎓 核心开发理念

### 1. Spec-Driven Development
**所有功能必须先创建 Spec，后编写代码。**

```
Spec Creation → Review → Implementation → Testing → Integration
```

每个 Spec 包含：
- `requirements.md` - 需求（User Stories + Acceptance Criteria）
- `design.md` - 设计（架构 + Schema + API）
- `tasks.md` - 任务（可执行的开发任务）

### 2. Schema-Driven Architecture
**Schema 就是法律。所有数据交互必须通过 Pydantic Schema。**

禁止使用 `dict` 传递数据，必须定义明确的 Schema：
- `RequirementPacket` - 输入
- `TicketScoreReport` - 输出
- `PRD_Draft` - 中间态
- `AgentState` - 状态

### 3. 分层架构
```
Application Layer (FastAPI)
    ↓
Configuration Layer (Settings)
    ↓
Schema Layer (Pydantic)
    ↓
Business Logic Layer (Agents, Gates)
    ↓
Infrastructure Layer (LLM, DB)
```

### 4. 质量优先
- **类型安全**: 所有函数必须有类型注解
- **测试覆盖**: 核心模块 > 80%
- **代码质量**: ruff + mypy 必须通过
- **配置外部化**: 不硬编码任何配置

---

## 🚦 下一步行动

### 如果你是 AI Assistant

#### 在 Kiro 中
```
1. "Show me the Phase 1 requirements"
2. "Execute task 1.1.1 from phase-1-foundation-scoring"
3. "Run all tasks for phase-1-foundation-scoring"
```

#### 在 Cursor 中
```
1. 打开 .kiro/specs/phase-1-foundation-scoring/tasks.md
2. 找到第一个未完成的任务 [ ]
3. 按照 design.md 实现该任务
4. 标记为完成 [x]
```

### 如果你是开发者

#### 第一次设置
```bash
# 1. 安装依赖
uv pip install -r requirements.txt
# 或
poetry install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY

# 3. 验证环境
python --version  # 应该是 3.14
pytest --version
ruff --version
```

#### 开始开发
```bash
# 1. 阅读 Spec
cat .kiro/specs/phase-1-foundation-scoring/requirements.md
cat .kiro/specs/phase-1-foundation-scoring/design.md
cat .kiro/specs/phase-1-foundation-scoring/tasks.md

# 2. 执行第一个任务（项目初始化）
# 按照 tasks.md 中的 Task 1.1 执行

# 3. 运行测试
pytest tests/ -v

# 4. 代码质量检查
ruff check src/ tests/
mypy src/
```

---

## 📖 学习路径

### 30 分钟快速上手
1. 阅读本文件（5 分钟）
2. 阅读 `.kiro/PROJECT_OVERVIEW.md`（15 分钟）
3. 浏览 Phase 1 的 `requirements.md`（10 分钟）

### 1 小时深入理解
1. 完成 30 分钟快速上手
2. 阅读 `SPEC_GUIDE.md`（10 分钟）
3. 阅读 `.kiro/steering/development-workflow.md`（15 分钟）
4. 阅读 Phase 1 的 `design.md`（15 分钟）

### 半天完整掌握
1. 完成 1 小时深入理解
2. 阅读 `.kiro/steering/schema-driven-rules.md`（30 分钟）
3. 阅读 `.kiro/steering/phase-execution-guide.md`（30 分钟）
4. 阅读 `docs/` 目录下的参考文档（1 小时）

---

## ⚠️ 重要约定

### ✅ 必须遵守
1. **Spec First**: 先有 Spec，后有代码
2. **Schema-Driven**: 所有数据用 Pydantic，禁止 dict
3. **Type Safety**: 所有函数必须有类型注解
4. **No Hardcode**: 配置通过环境变量，不硬编码
5. **Test Everything**: 核心逻辑必须有测试

### ❌ 禁止做法
1. 跳过 Spec 直接写代码
2. 使用 dict 传递数据
3. 函数没有类型注解
4. 硬编码 API Key 或配置
5. 不写测试

---

## 🆘 遇到问题？

### 常见问题

**Q: 我应该从哪里开始？**
A: 阅读本文件 → `.kiro/PROJECT_OVERVIEW.md` → `SPEC_GUIDE.md`

**Q: 如何执行任务？**
A: 查看 `.kiro/specs/phase-1-foundation-scoring/tasks.md`，按顺序执行

**Q: 如何判断任务是否完成？**
A: 所有 REQUIRED 任务标记为 `[x]`，且 Milestone 验收通过

**Q: 代码规范是什么？**
A: 查看 `.kiro/steering/development-workflow.md` 和 `.cursorrules`

**Q: Schema 怎么写？**
A: 查看 `.kiro/steering/schema-driven-rules.md`

### 问题升级

遇到以下情况立即停止并报告：
1. 连续 3 次测试失败
2. Spec 与实现严重不符
3. 发现架构级问题
4. 依赖冲突无法解决

---

## 🎯 成功标准

### Phase 1 完成标准
- [ ] 所有 35 个 REQUIRED 任务完成
- [ ] 所有测试通过（pytest）
- [ ] 代码质量检查通过（ruff + mypy）
- [ ] Milestone T1 验收通过
- [ ] 文档更新完整

### Milestone T1: The First Reject
- [ ] 输入一段烂需求（缺少 AC）
- [ ] 系统返回评分报告（JSON）
- [ ] `total_score < 60`
- [ ] `blocking_issues` 包含 `MISSING_AC`
- [ ] Hard Gate 返回 `REJECT`

---

## 📞 快速命令参考

### 开发命令
```bash
# 启动服务
uvicorn src.reqgate.app.main:app --reload --port 8000

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ tests/
ruff format src/ tests/
mypy src/

# 测试覆盖率
pytest tests/ --cov=src/reqgate --cov-report=html
```

### Spec 命令（在 Kiro 中）
```
# 查看需求
"Show me the requirements for phase-1-foundation-scoring"

# 执行单个任务
"Execute task 1.1.1 from phase-1-foundation-scoring"

# 执行所有任务
"Run all tasks for phase-1-foundation-scoring"

# 创建新 Spec
"Create a spec for phase-2-structuring-workflow"
```

---

## 🎉 准备好了吗？

### 下一步
1. ✅ 你已经读完了 `START_HERE.md`
2. 📖 现在去读 `.kiro/PROJECT_OVERVIEW.md`
3. 🚀 然后开始执行 Phase 1 任务

### 记住
- **Spec First, Code Second**
- **Schema is Law**
- **Quality over Speed**

---

**祝你开发顺利！如有疑问，随时查阅文档。** 🚀

Last Updated: 2025-01-21
Project Status: Phase 1 In Progress
