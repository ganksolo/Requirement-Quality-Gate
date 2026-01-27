# ReqGate 开发进度记录

> 本文档记录各 Phase 完成的功能模块，供团队参考。

---

## Phase 1: Foundation & Scoring Core

**状态**: ✅ 核心功能完成  
**更新日期**: 2026-01-22

### 已完成功能

| 层级 | 模块 | 功能描述 | 状态 |
|------|------|----------|------|
| **应用层** | `app/main.py` | FastAPI 应用入口，带生命周期管理 | ✅ |
| **API 层** | `api/routes.py` | `/health` 健康检查端点 | ✅ |
| **配置层** | `config/settings.py` | OpenRouter 统一 LLM 配置 | ✅ |
| **配置层** | `schemas/config.py` | `RubricScenarioConfig` 类型定义 | ✅ |
| **日志观测** | `observability/logging.py` | 结构化日志配置 | ✅ |
| **Schema 层** | `schemas/inputs.py` | `RequirementPacket` 输入验证 | ✅ |
| **Schema 层** | `schemas/outputs.py` | `TicketScoreReport` / `ReviewIssue` 评分报告 | ✅ |
| **Schema 层** | `schemas/internal.py` | `AgentState` 工作流状态 | ✅ |
| **业务逻辑** | `gates/rules.py` | `RubricLoader` YAML 评分规则加载器 | ✅ |
| **业务逻辑** | `gates/decision.py` | `HardGate` 门禁决策 (PASS/REJECT) + 决策日志 | ✅ |
| **LLM 适配器** | `adapters/llm.py` | `OpenRouterClient` + Fallback 支持 | ✅ |
| **评分代理** | `agents/scoring.py` | `ScoringAgent` 评分逻辑 + Prompt 工程 | ✅ |

### LLM 配置

| 配置项 | 值 |
|--------|-----|
| 主模型 | `deepseek/deepseek-chat` |
| 备用模型 | `google/gemini-2.0-flash-001` |
| API 网关 | OpenRouter |

### 测试覆盖

| 测试文件 | 测试数量 | 覆盖模块 |
|----------|---------|----------|
| `test_health.py` | 2 | Health 端点 |
| `test_settings.py` | 10 | 配置加载 |
| `test_schemas_inputs.py` | 17 | 输入 Schema 验证 |
| `test_schemas_outputs.py` | 14 | 输出 Schema 验证 |
| `test_rubric_loader.py` | 10 | 规则加载器 |
| `test_llm_adapter.py` | 6 | LLM 适配器 |
| `test_scoring_agent.py` | 6 | 评分代理 |
| `test_hard_gate.py` | 12 | 门禁决策 |
| `test_integration.py` | 5 | 端到端集成测试 |
| **总计** | **82** | - |

### 真实 LLM 测试验证

```
=== Real LLM Result ===
Score: 85
Ready: True
Blockers: 0
Summary: ## 评分结果 总分: 85/100
PASSED ✅ (4.8s)
```

### 人工测试命令

```bash
# 启动服务
uvicorn src.reqgate.app.main:app --reload --port 8000

# 健康检查
curl http://localhost:8000/health

# 运行测试
pytest tests/ -v

# LLM 连通性测试
python scripts/test_llm_connectivity.py

# 代码质量
ruff check src/ tests/
```

### 待完成任务

- [x] Milestone T1 验证 (第一次拒绝场景) → `scripts/verify_milestone_t1.py`
- [ ] `/score` API 端点 (移至 Phase 3)

---

## Phase 2: Multi-Agent Workflow

**状态**: ✅ 核心功能完成  
**更新日期**: 2026-01-27

### 已完成功能

| 层级 | 模块 | 功能描述 | 状态 |
|------|------|----------|------|
| **Schema 层** | `schemas/internal.py` | `PRD_Draft` 结构化 PRD 模型 | ✅ |
| **Schema 层** | `schemas/config.py` | `WorkflowConfig` 工作流配置 | ✅ |
| **工作流层** | `workflow/graph.py` | LangGraph DAG 工作流定义 | ✅ |
| **工作流层** | `workflow/errors.py` | 工作流异常类型定义 | ✅ |
| **工作流节点** | `workflow/nodes/input_guardrail.py` | 输入验证 + PII 检测 + 注入防护 | ✅ |
| **工作流节点** | `workflow/nodes/structuring_agent.py` | LLM 结构化提取 + 反幻觉检测 | ✅ |
| **工作流节点** | `workflow/nodes/structure_check.py` | Hard Check #1 结构完整性验证 | ✅ |
| **LLM 适配器** | `adapters/llm.py` | 重试逻辑 + `LLMClientWithRetry` | ✅ |
| **工作流逻辑** | `workflow/graph.py` | Fallback 降级机制 (-5 分惩罚) | ✅ |
| **配置层** | `config/settings.py` | Phase 2 环境变量扩展 | ✅ |

### 新增 Schema

| Schema | 描述 | 关键字段 |
|--------|------|----------|
| `PRD_Draft` | 结构化 PRD 草案 | `title`, `user_story`, `acceptance_criteria`, `missing_info` |
| `AgentState` | LangGraph 状态 | `structured_prd`, `fallback_activated`, `execution_times` |
| `WorkflowConfig` | 工作流配置 | `enable_guardrail`, `enable_structuring`, `enable_fallback` |
| `GuardrailResult` | 验证结果 | `passed`, `errors`, `warnings` |

### 工作流 DAG

```
[Input] → [Guardrail] → [Structuring Agent] → {Check}
                                                |
                               ┌────────────────┴────────────────┐
                               ↓ (PRD available)         ↓ (no PRD)
                       [Structure Check]           [Fallback]
                               ↓                         ↓
                          [Scoring] ←──────────────────┘
                               ↓
                            [Gate]
                               ↓
                           [Output]
```

### 错误类型

| 异常类 | 触发场景 |
|--------|----------|
| `WorkflowExecutionError` | 工作流执行基础异常 |
| `GuardrailRejectionError` | 输入被 Guardrail 拒绝 |
| `StructuringFailureError` | 结构化 Agent 提取失败 |
| `LLMTimeoutError` | LLM 调用超时 |
| `LLMRateLimitError` | LLM 调用被限流 |

### 测试覆盖

| 测试文件 | 测试数量 | 覆盖模块 |
|----------|---------|----------|
| `test_prd_draft.py` | 20 | PRD_Draft Schema |
| `test_agent_state.py` | 8 | AgentState TypedDict |
| `test_workflow_config.py` | 17 | WorkflowConfig 配置 |
| `test_input_guardrail.py` | 21 | 输入验证 + 安全检测 |
| `test_structuring_agent.py` | 22 | 结构化 Agent + 反幻觉 |
| `test_llm_retry.py` | 12 | 重试逻辑 |
| `test_workflow_errors.py` | 11 | 异常类型 |
| `test_workflow_graph.py` | 17 | LangGraph 节点 |
| `test_fallback.py` | 36 | Fallback 降级机制 |
| `test_workflow_integration.py` | 22 | 端到端工作流 |
| `test_structure_check.py` | 10 | Hard Check #1 结构验证 |
| **Phase 2 新增** | **196** | - |
| **总计 (含 Phase 1)** | **286** | - |

### Milestone 验证结果

| Milestone | 验证脚本 | 结果 |
|-----------|----------|------|
| **T2: End-to-End** | `scripts/milestone_t2_verification.py` | ✅ PASS (85/100, 10.49s) |
| **T2.1: Degradation** | `scripts/milestone_t2_1_verification.py` | ✅ PASS (Fallback 激活) |
| **T2.2: Structure Check** | Hard Check #1 节点实现 + 10 测试 | ✅ PASS (286/286 tests) |

### 人工测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 仅运行 Phase 2 测试
pytest tests/test_prd_draft.py tests/test_workflow_graph.py tests/test_fallback.py -v

# Milestone T2 验证 (需要 LLM API)
python scripts/milestone_t2_verification.py

# Milestone T2.1 验证 (使用 Mock)
python scripts/milestone_t2_1_verification.py

# 工作流逻辑快速测试
python -c "
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.workflow.graph import run_workflow

packet = RequirementPacket(
    raw_text='As a user, I want to reset my password via email so that I can regain access to my account. AC: User clicks forgot password, enters email, receives reset link.',
    source_type='Jira_Ticket',
    project_key='AUTH',
    ticket_type='Feature',
)

config = WorkflowConfig(enable_guardrail=True, enable_structuring=True)
result = run_workflow(packet, config)

print(f'PRD Title: {result[\"structured_prd\"].title if result[\"structured_prd\"] else \"N/A\"}')
print(f'Score: {result[\"score_report\"].total_score if result[\"score_report\"] else \"N/A\"}')
print(f'Decision: {\"PASS\" if result[\"gate_decision\"] else \"REJECT\"}')
print(f'Fallback: {result[\"fallback_activated\"]}')
"

# 代码质量检查
ruff check src/reqgate/workflow/ src/reqgate/schemas/
```

### 新增环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `ENABLE_STRUCTURING` | `true` | 启用结构化 Agent |
| `ENABLE_GUARDRAIL` | `true` | 启用输入验证 |
| `GUARDRAIL_MODE` | `lenient` | 验证严格程度 |
| `MAX_LLM_RETRIES` | `3` | LLM 重试次数 |
| `STRUCTURING_TIMEOUT` | `20` | 结构化超时 (秒) |

### 待完成任务

- [ ] `/workflow` API 端点
- [ ] 工作流可视化输出
- [ ] 性能基准测试

---

## Phase 3: Integration Layer

**状态**: ⏳ 待开始

> Phase 3 完成后在此补充记录

---

## Phase 4: Enhanced Intelligence

**状态**: ⏳ 待开始

> Phase 4 完成后在此补充记录
