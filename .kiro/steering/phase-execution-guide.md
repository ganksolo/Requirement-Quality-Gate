---
inclusion: always
---

# ReqGate 分阶段执行指南

## 项目分阶段策略

基于项目复杂度，将开发分为 **4 个 Phase**，每个 Phase 都是一个独立的 Spec。

## Phase 划分原则

1. **价值优先**：先实现核心价值（评分拦截），再完善辅助功能
2. **风险前置**：先解决技术难点（LLM 集成、Schema 设计）
3. **增量交付**：每个 Phase 都能独立运行和验证
4. **依赖最小**：Phase 之间依赖关系清晰，可并行开发

---

## Phase 1: Foundation & Scoring Core (地基与评分核心)

### 目标
构建最小可用的评分系统，能够对输入文本进行评分并做出拦截决策。

### 核心价值
- 验证 Schema-Driven 架构可行性
- 验证 LLM 评分准确性
- 建立项目基础设施

### Spec 名称
`phase-1-foundation-scoring`

### 交付物
1. **项目骨架**
   - FastAPI 应用框架
   - Pydantic Settings 配置管理
   - 基础日志和错误处理

2. **核心 Schema**
   - `RequirementPacket` (输入)
   - `TicketScoreReport` (输出)
   - `AgentState` (状态)

3. **评分规则配置**
   - `scoring_rubric.yaml` (FEATURE/BUG 规则)
   - 规则加载器

4. **Scoring Agent**
   - LLM 适配器 (OpenAI/Gemini)
   - Scoring Agent 节点
   - Prompt 模板管理

5. **Hard Gate**
   - 门禁决策逻辑
   - 拦截规则实现

6. **基础测试**
   - Schema 验证测试
   - Scoring Agent 单元测试
   - Hard Gate 逻辑测试

### 验收标准 (Milestone T1) ✅
- [x] 输入一段文本，返回 JSON 格式的评分报告
- [x] 缺少 AC 的需求被正确识别为 BLOCKER
- [x] 分数 < 60 的需求被 Hard Gate 拦截
- [x] 所有测试通过

### 不包含的内容
- ❌ Structuring Agent（Phase 2）
- ❌ LangGraph 工作流（Phase 2）
- ❌ FastAPI 路由（Phase 3）
- ❌ Jira/n8n 集成（Phase 3）

---

## Phase 2: Structuring & Workflow Pipeline (结构化与工作流)

### 目标
添加结构化能力，将非结构化输入转化为标准 PRD，并串联完整的 LangGraph 工作流。

### 核心价值
- 解决 PM "不会写文档" 的问题
- 建立完整的数据处理管线
- 实现容错和降级机制

### Spec 名称
`phase-2-structuring-workflow`

### 依赖
- Phase 1 完成

### 交付物
1. **PRD Schema**
   - `PRD_Draft` (结构化草稿)
   - 字段验证规则

2. **Structuring Agent**
   - Structuring Agent 节点
   - Prompt 模板（提取 User Story/AC）
   - 幻觉防护机制

3. **Input Guardrail**
   - 输入长度检查
   - PII 过滤
   - Prompt 注入防护

4. **LangGraph 工作流**
   - DAG 定义
   - 节点串联逻辑
   - 状态管理

5. **容错机制**
   - Structuring 失败降级
   - LLM 超时重试
   - 错误日志记录

6. **集成测试**
   - 端到端工作流测试
   - 降级场景测试

### 验收标准 (Milestone T2)
- [ ] 输入 300 字会议纪要，生成结构化 PRD
- [ ] Structuring 失败时，系统降级到直接评分
- [ ] 完整工作流无崩溃运行
- [ ] 所有节点测试通过

### 不包含的内容
- ❌ HTTP API（Phase 3）
- ❌ 外部集成（Phase 3）
- ❌ 数据持久化（Phase 4）

---

## Phase 3: API & Integration (接口与集成)

### 目标
将 Python 工作流封装为 HTTP API，并集成 Jira/n8n，让 PM 能够实际使用。

### 核心价值
- 系统可被外部调用
- PM 可通过 Jira 触发检查
- 自动化反馈闭环

### Spec 名称
`phase-3-api-integration`

### 依赖
- Phase 2 完成

### 交付物
1. **FastAPI 路由**
   - `POST /v1/workflow/run` (执行工作流)
   - `GET /v1/health` (健康检查)
   - `GET /v1/metrics` (基础指标)

2. **请求/响应处理**
   - 请求验证
   - 响应格式化
   - 错误处理

3. **Output Formatter**
   - JSON → Markdown 转换
   - Emoji 和格式美化
   - 多语言支持（可选）

4. **n8n 集成方案**
   - Webhook 配置文档
   - n8n 工作流模板
   - 回调处理

5. **Jira 适配器**
   - Jira API 封装
   - 评论回写
   - 状态流转

6. **API 测试**
   - FastAPI TestClient 测试
   - 集成测试
   - 性能测试（基础）

### 验收标准 (Milestone T3)
- [ ] 通过 HTTP API 调用工作流成功
- [ ] 在 Jira Sandbox 创建 Ticket，触发检查
- [ ] 30 秒内收到格式化的评论回复
- [ ] API 响应时间 < 60s (P95)

### 不包含的内容
- ❌ 数据库持久化（Phase 4）
- ❌ 监控面板（Phase 4）
- ❌ 黄金测试集（Phase 4）

---

## Phase 4: Operations & Optimization (运营与优化)

### 目标
建立生产级的运维能力，包括数据持久化、监控、反馈闭环和持续优化。

### 核心价值
- 系统可追溯
- 误判可修正
- 持续改进

### Spec 名称
`phase-4-operations-optimization`

### 依赖
- Phase 3 完成

### 交付物
1. **数据持久化**
   - PostgreSQL Schema 设计
   - `workflow_runs` 表
   - `audit_logs` 表
   - `eval_datasets` 表

2. **数据访问层**
   - SQLAlchemy Models
   - Repository 模式
   - 数据库迁移 (Alembic)

3. **监控与追踪**
   - LangSmith 集成（可选）
   - OpenTelemetry 追踪
   - 指标收集（reject_rate, latency）

4. **黄金测试集**
   - 20 个好样本
   - 20 个坏样本
   - 回归测试脚本

5. **反馈闭环**
   - 误判标记机制
   - 人工复盘流程
   - Prompt 版本管理

6. **性能优化**
   - LLM 调用优化
   - 缓存策略
   - 并发处理

7. **运维文档**
   - 部署指南
   - 故障排查手册
   - 监控面板配置

### 验收标准 (Milestone T4)
- [ ] 连续运行 3 天，处理 50+ 需求
- [ ] 系统可用性 > 99%
- [ ] 误判率 < 10%
- [ ] 所有运行记录可追溯

---

## Phase 执行顺序

```
Phase 1 (Week 1)
   ↓
Phase 2 (Week 2)
   ↓
Phase 3 (Week 3)
   ↓
Phase 4 (Week 4+)
```

### 并行开发可能性

- **Phase 1 + Phase 2**：可部分并行（Schema 设计可提前）
- **Phase 3 + Phase 4**：不建议并行（需要稳定的 API）

---

## Spec 创建顺序

### 第一步：创建 Phase 1 Spec
```
"Create a spec for phase-1-foundation-scoring based on the project documentation"
```

### 第二步：执行 Phase 1 任务
```
"Run all tasks for phase-1-foundation-scoring"
```

### 第三步：验收 Phase 1
```
"Verify Phase 1 milestone T1 is met"
```

### 第四步：创建 Phase 2 Spec
```
"Create a spec for phase-2-structuring-workflow"
```

### 重复直到 Phase 4 完成

---

## 跨 Phase 的共享资源

### 共享配置
- `.env.example`
- `pyproject.toml`
- `config/scoring_rubric.yaml`
- `config/guardrail_config.yaml` (Phase 2+)

### 共享文档
- `docs/architecture.md`
- `docs/schemas.md`
- `docs/workflow.md`
- `prompts/` (Phase 2+)

### 共享代码
- `src/reqgate/schemas/` (Phase 1 定义，后续扩展)
- `src/reqgate/config/` (Phase 1 定义，后续扩展)
- `src/reqgate/adapters/llm.py` (Phase 1 定义，Phase 2 扩展 retry 逻辑)
- `src/reqgate/workflow/` (Phase 2 新增)

---

## Phase 切换检查清单

在开始下一个 Phase 前，确保：

- [ ] 当前 Phase 所有 REQUIRED 任务完成
- [ ] 当前 Phase Milestone 验收通过
- [ ] 所有测试通过
- [ ] 代码已合并到 develop 分支
- [ ] 文档已更新
- [ ] 团队 review 通过

---

## 风险管理

### Phase 1 风险
- **风险**：LLM 评分不准确
- **应对**：建立小规模测试集，快速迭代 Prompt

### Phase 2 风险
- **风险**：Structuring Agent 产生幻觉
- **应对**：强约束 Prompt，添加验证逻辑

### Phase 3 风险
- **风险**：LLM 响应超时（> 60s）
- **应对**：实现异步回调机制

### Phase 4 风险
- **风险**：误判率过高，PM 抵触
- **应对**：提供人工强制通过按钮，分级策略

---

## 快速参考

### 当前应该做什么？

1. **如果项目刚开始** → 创建 Phase 1 Spec
2. **如果 Phase 1 Spec 已创建** → 执行 Phase 1 任务
3. **如果 Phase 1 已完成** → 验收 Milestone T1，然后创建 Phase 2 Spec ✅ 当前状态
4. **如果 Phase 2 Spec 已创建** → 执行 Phase 2 任务 👉 **执行此步**
5. **如果所有 Phase 完成** → 进入维护模式，处理 Bug 和优化

### 如何判断 Phase 是否完成？

- 所有 REQUIRED 任务状态为 `[x]`
- Milestone 验收标准全部满足
- 测试通过率 100%

---

**记住：一次只专注一个 Phase，不要跨 Phase 开发。**
