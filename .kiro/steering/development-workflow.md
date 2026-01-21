---
inclusion: always
---

# ReqGate 开发工作流规范

## 项目概述

ReqGate 是一个基于 LangGraph 的需求质量门禁系统，采用 Spec-Driven Development 方法论进行开发。

## 开发流程 (Development Workflow)

### 1. Spec-First 原则

**所有功能开发必须先创建 Spec，后编写代码。**

```
Spec Creation → Review → Implementation → Testing → Integration
```

### 2. Spec 文件结构

每个 spec 必须包含三个文件：

```
.kiro/specs/{feature-name}/
├── requirements.md    # 需求定义（User Stories + Acceptance Criteria）
├── design.md         # 设计文档（架构、数据契约、API 设计）
└── tasks.md          # 任务清单（可执行的开发任务）
```

### 3. 任务执行规则

#### 单任务执行模式
- 一次只执行一个任务
- 完成后停止，等待人工 review
- 不自动继续下一个任务

#### 批量执行模式
- 使用 "run all tasks" 命令
- 按顺序执行所有未完成的 REQUIRED 任务
- 遇到错误立即停止并报告

### 4. 任务状态标记

```markdown
- [ ] 未开始 (Not Started)
- [~] 已排队 (Queued)
- [-] 进行中 (In Progress)
- [x] 已完成 (Completed)
- [ ]* 可选任务 (Optional - 带星号)
```

### 5. 代码质量要求

#### 必须遵守的规则
1. **类型安全**：所有函数必须有类型注解
2. **Schema-Driven**：使用 Pydantic 定义所有数据契约
3. **配置外部化**：所有配置通过环境变量或 YAML 文件管理
4. **测试覆盖**：核心逻辑必须有单元测试
5. **错误处理**：显式处理所有异常情况

#### 代码风格
- 使用 `ruff` 进行 lint 和 format
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 规范

### 6. 测试策略

#### 测试层级
1. **单元测试** (Unit Tests)
   - 测试单个函数/类的行为
   - 使用 pytest
   - 文件命名：`test_*.py`

2. **集成测试** (Integration Tests)
   - 测试组件间的交互
   - 测试 LangGraph 工作流
   - 文件命名：`test_integration_*.py`

3. **端到端测试** (E2E Tests)
   - 测试完整的 API 流程
   - 使用 FastAPI TestClient
   - 文件命名：`test_e2e_*.py`

#### 测试原则
- 先写测试，后写实现（TDD 可选但推荐）
- 测试必须可重复执行
- 不使用 mock 除非必要（优先真实依赖）
- 测试失败必须修复，不能跳过

### 7. Git 工作流

#### 分支策略
```
main (生产)
  ├── develop (开发主线)
  │   ├── feature/phase-1-foundation
  │   ├── feature/phase-2-agents
  │   └── feature/phase-3-integration
```

#### Commit 规范
```
<type>(<scope>): <subject>

type: feat, fix, docs, style, refactor, test, chore
scope: 功能模块名称
subject: 简短描述（50字符内）

示例：
feat(scoring-agent): implement rubric-based scoring logic
fix(schema): add missing validation for RequirementPacket
docs(spec): update phase-1 requirements
test(gates): add hard gate decision tests
```

### 8. 依赖管理

#### 使用 uv（优先）
```bash
# 安装依赖
uv pip install -r requirements.txt

# 添加新依赖
uv pip install <package>
uv pip freeze > requirements.txt
```

#### 或使用 poetry（备选）
```bash
# 安装依赖
poetry install

# 添加新依赖
poetry add <package>
```

### 9. 环境配置

#### 必需的环境变量
```bash
# .env (本地开发，不提交)
REQGATE_ENV=development
REQGATE_PORT=8000
LOG_LEVEL=INFO

# LLM API Keys
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=xxx

# Database (Phase 4)
DATABASE_URL=postgresql://localhost/reqgate
```

#### 配置优先级
```
环境变量 > .env 文件 > 默认值
```

### 10. 文档更新规则

#### 必须更新文档的情况
1. 添加新的 API 端点 → 更新 `docs/api.md`
2. 修改数据 Schema → 更新 `docs/schemas.md`
3. 改变工作流逻辑 → 更新 `docs/workflow.md`
4. 架构决策 → 记录到 `docs/decisions.md`

#### 文档格式
- 使用 Markdown
- 包含代码示例
- 保持简洁清晰

### 11. Code Review 检查清单

在提交 PR 前，确保：

- [ ] 代码通过 `ruff check` 和 `ruff format`
- [ ] 代码通过 `mypy` 类型检查
- [ ] 所有测试通过 `pytest`
- [ ] 更新了相关文档
- [ ] 添加了必要的注释
- [ ] 没有硬编码的配置值
- [ ] 错误处理完整
- [ ] 符合 Spec 中的设计

### 12. 跨 IDE 协作规则

#### Kiro (Antigravity) 使用场景
- Spec 创建和规划
- 复杂的重构任务
- 多文件协同修改
- 工作流编排

#### Cursor 使用场景
- 快速代码编写
- 单文件修改
- 调试和问题修复
- 代码补全

#### 协作约定
1. **共享 Spec**：两个 IDE 都必须遵循 `.kiro/specs/` 中的规范
2. **统一配置**：使用相同的 `.env.example` 和 `pyproject.toml`
3. **同步状态**：修改 `tasks.md` 后及时同步
4. **避免冲突**：不同 IDE 处理不同的 Phase/Feature

### 13. 阶段交付标准

每个 Phase 完成后必须满足：

1. **所有 REQUIRED 任务完成**
2. **测试通过率 100%**
3. **文档更新完整**
4. **代码 review 通过**
5. **Milestone 验收通过**

### 14. 问题升级机制

遇到以下情况立即停止并报告：

1. **连续 3 次测试失败**
2. **Spec 与实现严重不符**
3. **发现架构级问题**
4. **依赖冲突无法解决**
5. **性能指标不达标**

## 快速参考

### 常用命令
```bash
# 启动开发服务器
uvicorn src.reqgate.app.main:app --reload --port 8000

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ tests/
mypy src/

# 格式化代码
ruff format src/ tests/
```

### Spec 命令
```bash
# 创建新 spec
"Create a spec for [feature-name]"

# 执行单个任务
"Execute task 1.1 from [spec-name]"

# 执行所有任务
"Run all tasks for [spec-name]"
```

---

**记住：Spec First, Code Second. 质量优于速度。**
