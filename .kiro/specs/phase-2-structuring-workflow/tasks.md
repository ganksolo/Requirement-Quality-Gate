# Phase 2: Structuring & Workflow Pipeline - Tasks

## Task Overview

Total Tasks: 47 (43 Required + 4 Optional)
Estimated Time: 1 Week

> **Note**: 5 new tasks added for Phase 1 backward compatibility verification (1.1.7, 1.3.5, 4.1.8, 8.1.7, 8.1.8)

## 1. Schema Extensions

### 1.1 Define PRD_Draft Schema
- [x] 1.1.1 Extend src/reqgate/schemas/internal.py with PRD_Draft class (file exists from Phase 1)
- [x] 1.1.2 Add all required fields (title, user_story, acceptance_criteria, etc.)
- [x] 1.1.3 Add validators for title length and format
- [x] 1.1.4 Add validators for user_story format
- [x] 1.1.5 Add example to schema Config
- [x] 1.1.6 Create tests/test_prd_draft_schema.py with validation tests
- [x] 1.1.7 Verify Phase 1 tests still pass after schema extension

### 1.2 Extend AgentState
- [x] 1.2.1 Update AgentState in src/reqgate/schemas/internal.py
- [x] 1.2.2 Add structured_prd field (Optional[PRD_Draft])
- [x] 1.2.3 Add fallback_activated field (bool)
- [x] 1.2.4 Add execution_times field (dict[str, float])
- [x] 1.2.5 Update schemas/__init__.py to export PRD_Draft

### 1.3 Define Workflow Configuration Schema
- [x] 1.3.1 Extend src/reqgate/schemas/config.py with WorkflowConfig class (file exists, contains RubricScenarioConfig)
- [x] 1.3.2 Implement WorkflowConfig class with all configuration fields
- [x] 1.3.3 Add configuration fields (enable_guardrail, max_retries, etc.)
- [x] 1.3.4 Create tests/test_workflow_config.py
- [x] 1.3.5 Update schemas/__init__.py to export WorkflowConfig

## 2. Input Guardrail

### 2.1 Create Guardrail Configuration
- [x] 2.1.1 Create config/guardrail_config.yaml
- [x] 2.1.2 Define length constraints (min_length, max_length)
- [x] 2.1.3 Define PII detection patterns
- [x] 2.1.4 Define prompt injection patterns
- [x] 2.1.5 Add configuration modes (strict/lenient)

### 2.2 Implement Guardrail Logic
- [x] 2.2.1 Create src/reqgate/workflow/__init__.py
- [x] 2.2.2 Create src/reqgate/workflow/nodes/__init__.py
- [x] 2.2.3 Create src/reqgate/workflow/nodes/input_guardrail.py
- [x] 2.2.4 Implement length validation
- [x] 2.2.5 Implement PII detection (regex-based)
- [x] 2.2.6 Implement prompt injection detection
- [x] 2.2.7 Implement guardrail configuration loader
- [x] 2.2.8 Create tests/test_input_guardrail.py

### 2.3 Guardrail Error Handling
- [x] 2.3.1 Define GuardrailRejectionError in src/reqgate/workflow/errors.py
- [x] 2.3.2 Implement error logging
- [x] 2.3.3 Add tests for rejection scenarios

## 3. Structuring Agent

### 3.1 Create Prompt Template
- [x] 3.1.1 Create prompts/ directory
- [x] 3.1.2 Create prompts/structuring_agent_v1.txt
- [x] 3.1.3 Write anti-hallucination instructions
- [x] 3.1.4 Add extraction guidelines
- [x] 3.1.5 Add example output

### 3.2 Implement Structuring Agent
- [x] 3.2.1 Create src/reqgate/workflow/nodes/structuring_agent.py
- [x] 3.2.2 Implement prompt loading and formatting
- [x] 3.2.3 Implement LLM call with PRD_Draft schema
- [x] 3.2.4 Implement output validation
- [x] 3.2.5 Implement anti-hallucination validation
- [x] 3.2.6 Add error handling for LLM failures
- [x] 3.2.7 Create tests/test_structuring_agent.py

### 3.3 Structuring Agent Tests
- [x] 3.3.1 Test extraction from well-formatted text
- [x] 3.3.2 Test extraction from messy meeting transcript
- [x] 3.3.3 Test handling of missing AC
- [x] 3.3.4 Test missing_info detection
- [x] 3.3.5 Test clarification_questions generation
- [x] 3.3.6 Test anti-hallucination (no invented content)

## 4. LLM Retry Logic

### 4.1 Extend LLM Adapter
- [x] 4.1.1 Check if tenacity is already a dependency, add to pyproject.toml if not
- [x] 4.1.2 Extend src/reqgate/adapters/llm.py (keep existing LLMClient unchanged)
- [x] 4.1.3 Implement call_llm_with_retry function
- [x] 4.1.4 Add exponential backoff configuration
- [x] 4.1.5 Add timeout handling
- [x] 4.1.6 Add rate limit handling
- [x] 4.1.7 Create tests/test_llm_retry.py
- [x] 4.1.8 Verify Phase 1 LLM tests still pass

### 4.2 Define LLM Error Types
- [x] 4.2.1 Create LLMTimeoutError in src/reqgate/workflow/errors.py (already created in Section 2)
- [x] 4.2.2 Create LLMRateLimitError (already created in Section 2)
- [x] 4.2.3 Add error logging

## 5. LangGraph Workflow

### 5.1 Setup LangGraph
- [x] 5.1.1 Add langgraph dependency to pyproject.toml (already present)
- [x] 5.1.2 Create src/reqgate/workflow/graph.py
- [x] 5.1.3 Import StateGraph and END from langgraph

### 5.2 Implement Workflow Nodes
- [x] 5.2.1 Create input_guardrail_node wrapper (already in Section 2)
- [x] 5.2.2 Create structuring_agent_node wrapper (already in Section 3)
- [x] 5.2.3 Update scoring_agent_node to handle fallback mode
- [x] 5.2.4 Create hard_gate_node wrapper
- [x] 5.2.5 Add execution time tracking to each node

### 5.3 Define Workflow Graph
- [x] 5.3.1 Implement create_workflow() function
- [x] 5.3.2 Add all nodes to StateGraph
- [x] 5.3.3 Define linear edges (guardrail → structuring → scoring → gate)
- [x] 5.3.4 Implement should_fallback() routing function
- [x] 5.3.5 Add conditional edge for fallback logic
- [x] 5.3.6 Compile workflow graph

### 5.4 Workflow Execution
- [x] 5.4.1 Implement run_workflow() function
- [x] 5.4.2 Initialize AgentState from RequirementPacket
- [x] 5.4.3 Execute workflow graph
- [x] 5.4.4 Handle workflow exceptions
- [x] 5.4.5 Return final AgentState

## 6. Fallback Mechanism

### 6.1 Implement Fallback Logic
- [x] 6.1.1 Update scoring_agent_node to detect missing structured_prd (done in Section 5)
- [x] 6.1.2 Implement format_prd_for_scoring() helper (done in Section 5)
- [x] 6.1.3 Implement fallback mode (use raw_text) (done in Section 5)
- [x] 6.1.4 Set fallback_activated flag (done in Section 5)
- [x] 6.1.5 Log fallback activation (done in Section 5)
- [x] 6.1.6 Apply score penalty for fallback mode (-5 points)

### 6.2 Fallback Tests
- [x] 6.2.1 Create tests/test_fallback.py
- [x] 6.2.2 Test fallback activation on structuring failure
- [x] 6.2.3 Test scoring continues with raw text
- [x] 6.2.4 Test fallback flag is set correctly
- [x] 6.2.5 Test score penalty is applied

## 7. Integration & Testing

### 7.1 Workflow Integration Tests
- [x] 7.1.1 Create tests/test_workflow_integration.py
- [x] 7.1.2 Test happy path (all nodes succeed)
- [x] 7.1.3 Test fallback path (structuring fails)
- [x] 7.1.4 Test retry path (LLM timeout then success)
- [x] 7.1.5 Test error path (guardrail rejects input)
- [x] 7.1.6 Verify state transitions
- [x] 7.1.7 Verify execution times logged

### 7.2 End-to-End Tests
- [x] 7.2.1 Test with meeting transcript input
- [x] 7.2.2 Test with well-formatted PRD input
- [x] 7.2.3 Test with malformed input
- [x] 7.2.4 Test with PII-containing input
- [x] 7.2.5 Test with prompt injection attempt

### 7.3 Code Quality
- [x] 7.3.1 Run ruff check and fix all issues
- [x] 7.3.2 Run ruff format on all code
- [x] 7.3.3 Run mypy and fix type errors (existing issues in project, not from Phase 2)
- [x] 7.3.4 Ensure all tests pass with pytest (276 tests passed)

## 8. Configuration & Documentation

### 8.1 Configuration Updates
- [x] 8.1.1 Update .env.example with Phase 2 variables
- [x] 8.1.2 Extend src/reqgate/config/settings.py (keep existing fields unchanged)
- [x] 8.1.3 Add enable_structuring setting with default True
- [x] 8.1.4 Add enable_guardrail setting with default True
- [x] 8.1.5 Add max_llm_retries setting with default 3
- [x] 8.1.6 Add structuring_timeout setting with default 20
- [x] 8.1.7 Add guardrail_config_path setting
- [x] 8.1.8 Verify Phase 1 settings tests still pass

### 8.2 Documentation
- [x] 8.2.1 Update docs/architecture.md with workflow diagram
- [x] 8.2.2 Update docs/workflow.md with LangGraph details
- [x] 8.2.3 Create docs/prompts.md documenting prompt templates
- [x] 8.2.4 Update README.md with Phase 2 features

## 9. Milestone Verification

### 9.1 Milestone T2: End-to-End Workflow
- [x] 9.1.1 Prepare meeting transcript sample (300 words)
- [x] 9.1.2 Create test script to run complete workflow
- [x] 9.1.3 Verify PRD_Draft is generated
- [x] 9.1.4 Verify PRD_Draft contains User Story and AC
- [x] 9.1.5 Verify Scoring Agent uses PRD_Draft
- [x] 9.1.6 Verify Hard Gate makes correct decision
- [x] 9.1.7 Verify workflow completes in < 60s
- [x] 9.1.8 Document test results

### 9.2 Milestone T2.1: Degradation Test
- [x] 9.2.1 Create test script with mocked structuring failure
- [x] 9.2.2 Verify workflow doesn't crash
- [x] 9.2.3 Verify Scoring Agent uses raw text
- [x] 9.2.4 Verify score penalty applied
- [x] 9.2.5 Verify error logged
- [x] 9.2.6 Document test results

## Task Dependencies

```
1.1 → 1.2 → 1.3
1.2 → 2.1 → 2.2 → 2.3
1.2 → 3.1 → 3.2 → 3.3
2.2 → 4.1 → 4.2
3.2 + 4.1 → 5.1 → 5.2 → 5.3 → 5.4
5.4 → 6.1 → 6.2
6.2 → 7.1 → 7.2 → 7.3
7.3 → 8.1 → 8.2 → 9.1 → 9.2
```

## Execution Notes

### Priority Order
1. **Critical Path**: 1.1 → 1.2 → 3.1 → 3.2 → 5.1 → 5.2 → 5.3 → 5.4 → 9.1
2. **Guardrail**: 2.1 → 2.2 → 2.3 (can be done in parallel with Structuring)
3. **Retry Logic**: 4.1 → 4.2 (can be done in parallel)
4. **Testing**: Can be done incrementally with implementation

### Estimated Time per Section
- Section 1 (Schemas): 3 hours
- Section 2 (Guardrail): 4 hours
- Section 3 (Structuring): 6 hours
- Section 4 (Retry): 2 hours
- Section 5 (LangGraph): 5 hours
- Section 6 (Fallback): 3 hours
- Section 7 (Testing): 5 hours
- Section 8 (Config/Docs): 2 hours
- Section 9 (Milestones): 2 hours

**Total: ~32 hours (4-5 days)**

### Testing Strategy
- Write tests immediately after implementing each component
- Use pytest fixtures for common test data
- Mock LLM calls in unit tests
- Use real LLM calls only in integration tests (optional)
- Test fallback scenarios explicitly

### Code Review Checklist
Before marking Phase 2 complete:
- [ ] All required tasks completed
- [ ] All tests passing (including all 82 Phase 1 tests)
- [ ] Code quality checks passing (ruff, mypy)
- [ ] Documentation updated
- [ ] Milestone T2 and T2.1 verified
- [ ] No hardcoded secrets or API keys
- [ ] All schemas have docstrings
- [ ] Error handling implemented
- [ ] Retry logic tested
- [ ] Fallback mechanism tested
- [ ] All Phase 1 APIs unchanged (ScoringAgent.score, HardGate.decide)

## Optional Enhancements

### Optional Tasks
- [ ]*3.2.8 Add confidence scoring to extracted fields
- [ ]*5.4.6 Add workflow visualization/debugging output
- [ ]*7.2.6 Add performance benchmarking tests
- [ ]*8.2.5 Create workflow diagram with mermaid

## Next Steps After Phase 2

Once Phase 2 is complete and Milestones T2/T2.1 are verified:
1. Review and document lessons learned
2. Optimize prompt templates based on test results
3. Create Phase 3 spec (API & Integration)
4. Plan Phase 3 implementation

## Notes

### Key Differences from Phase 1
- Introduces LangGraph for workflow orchestration
- Adds Structuring Agent (new LLM component)
- Implements fallback and retry mechanisms
- More complex state management
- More integration testing required

### Integration with Phase 1
- Reuses all Phase 1 schemas (RequirementPacket, TicketScoreReport)
- Reuses LLM adapter (extends with retry logic)
- Reuses Scoring Agent (updates to handle fallback mode)
- Reuses Hard Gate (no changes needed)
- Reuses configuration system (extends with new settings)

### Common Pitfalls to Avoid
1. **Hallucination**: Ensure Structuring Agent doesn't invent information
2. **State Mutation**: LangGraph nodes should not mutate state in place
3. **Error Swallowing**: Always log errors before fallback
4. **Timeout Handling**: Set reasonable timeouts for LLM calls
5. **Schema Validation**: Always validate LLM outputs against schemas


---

## 10. 白皮书合规性修复 (Compliance Updates)

### 背景

基于 `requirements/manual_reports.md.md` 的评测结果，Phase 2 需要补充以下功能以符合白皮书 4.2 核心节点要求。

**目标**：将白皮书合规度从 80% 提升到 95%+

### 10.1 Hard Check #1 节点实现

- [x] 10.1.1 创建 src/reqgate/workflow/nodes/structure_check.py
- [x] 10.1.2 实现 hard_check_structure_node() 函数
- [x] 10.1.3 添加 AC 数量检查（>= 2）
- [x] 10.1.4 添加 User Story 格式检查（>= 20 字符）
- [x] 10.1.5 添加 Title 规范检查（10-200 字符，动词开头）
- [x] 10.1.6 更新 AgentState 添加 structure_check_passed 和 structure_errors 字段
- [x] 10.1.7 创建 tests/test_structure_check.py

### 10.2 Hard Check #1 测试

- [x] 10.2.1 测试合法 PRD 通过检查
- [x] 10.2.2 测试 AC 数量不足被拦截
- [x] 10.2.3 测试 User Story 缺失被拦截
- [x] 10.2.4 测试 Title 过短被拦截
- [x] 10.2.5 测试 Title 格式建议（动词开头）
- [x] 10.2.6 测试 Structuring 失败时跳过检查

### 10.3 集成 Hard Check #1 到工作流

- [x] 10.3.1 更新 src/reqgate/workflow/graph.py
- [x] 10.3.2 在 create_workflow() 中添加 structure_check 节点
- [x] 10.3.3 更新 should_check_structure() 路由函数
- [x] 10.3.4 添加 structuring → structure_check 的条件边
- [x] 10.3.5 添加 structure_check → scoring 的边
- [x] 10.3.6 更新 execution_times 记录 structure_check 节点

### 10.4 文档更新

- [x] 10.4.1 更新 design.md 添加 Hard Check #1 设计 (已存在于 design.md L956-1312)
- [x] 10.4.2 更新 design.md 添加 7 节点映射表 (已存在于 design.md L1116-1124)
- [x] 10.4.3 更新 design.md 澄清 Normalize = RequirementPacket Schema (已存在于 design.md L1207-1249)
- [x] 10.4.4 更新 design.md 的 LangGraph DAG 图（包含 7 个节点）(已存在于 design.md L1096-1112)
- [x] 10.4.5 更新 requirements.md 添加 US-5.1 和 AC-12/13/14 (已存在于 L241-271)
- [x] 10.4.6 更新 docs/architecture.md 标注完整的 7 个节点
- [x] 10.4.7 更新 docs/workflow.md 说明 Normalize 实现方式

### 10.5 集成测试更新

- [x] 10.5.1 更新 tests/test_workflow_integration.py
- [x] 10.5.2 添加 7 节点完整性测试
- [x] 10.5.3 验证 execution_times 包含 structure_check
- [x] 10.5.4 验证节点执行顺序正确
- [x] 10.5.5 测试 Hard Check #1 拦截低质量 PRD

### 10.6 Milestone T2.2: 白皮书合规性验证

- [x] 10.6.1 对照白皮书 4.2 核心节点清单
- [x] 10.6.2 验证 7 个节点全部实现
- [x] 10.6.3 验证架构文档完整性 (design.md 已更新)
- [x] 10.6.4 运行所有测试确保通过 (286/286 passed)
- [x] 10.6.5 生成合规性报告（更新 docs/PROGRESS.md）
- [x] 10.6.6 确认白皮书合规度 >= 95%

## Task Dependencies Update

```
原有依赖保持不变
9.2 → 10.1 → 10.2 → 10.3 → 10.4 → 10.5 → 10.6
```

## Execution Notes Update

### 新增时间估算

- Section 10 (合规性修复): 1.5-2 天
  - 10.1-10.2 (Hard Check #1 实现): 4 hours
  - 10.3 (工作流集成): 2 hours
  - 10.4 (文档更新): 2 hours
  - 10.5 (集成测试): 2 hours
  - 10.6 (验收): 2 hours

**更新后总计: ~34 hours (4.5-5 days)**

### 优先级

**P0 - 必须完成（阻塞人工测试）**:
- 10.1 Hard Check #1 实现
- 10.2 Hard Check #1 测试
- 10.3 工作流集成
- 10.5 集成测试更新

**P1 - 建议完成（提升测试体验）**:
- 10.4 文档更新
- 10.6 合规性验证

### Code Review Checklist Update

在标记 Phase 2 完成前，额外确认：

- [x] Hard Check #1 节点已实现并测试通过
- [x] 7 个节点全部在工作流中可见
- [x] 文档明确说明 Normalize 实现方式 (design.md L1207-1249)
- [x] 架构图标注完整的 7 个节点 (design.md L1096-1112)
- [x] 白皮书合规度 >= 95%
- [x] Milestone T2.2 验收通过 (286/286 tests)

## Notes Update

### 白皮书合规性说明

**修复前的状态**：
- 6/7 节点实现（缺 Hard Check #1）
- Normalize 节点实现方式不明确
- 白皮书合规度 ~80%

**修复后的状态**：
- 7/7 节点完整实现
- Normalize 通过 Schema 实现（文档明确）
- 白皮书合规度 ~95%

**不在 Phase 2 修复的问题**：
- Jira 回写（Phase 3）
- Reject 计数器（Phase 3）
- Formatter 独立节点（Phase 3）
- Golden Set（Phase 4）
- Rubric 版本管理（Phase 4）

### 关键设计决策

**Decision: Hard Check #1 的位置**

放在 Structuring 和 Scoring 之间，原因：
1. 符合白皮书节点顺序
2. 在结构化后立即验证质量
3. 避免低质量 PRD 进入评分
4. 不影响 fallback 机制

**Decision: Normalize 不创建独立节点**

通过 RequirementPacket Schema 实现，原因：
1. Schema-Driven 原则的体现
2. Pydantic validators 自动标准化
3. 避免冗余代码
4. 符合"输入验证在 Schema 层"的设计

### 测试策略更新

新增测试场景：
1. Hard Check #1 拦截低质量 PRD
2. 7 节点完整性验证
3. Normalize 功能验证（通过 Schema 测试）

### 常见问题

**Q: 为什么 Normalize 不是独立节点？**
A: Normalize 通过 RequirementPacket Schema 的 validators 实现，这是 Schema-Driven 架构的自然体现。

**Q: Hard Check #1 会影响性能吗？**
A: 不会。Hard Check #1 是纯逻辑检查（5-10ms），不调用 LLM，性能影响可忽略。

**Q: 如果 Hard Check #1 失败，工作流会中断吗？**
A: 不会。工作流继续执行，但会在 state 中记录 `structure_check_passed = False` 和具体错误，Scoring Agent 可以根据此信息扣分。
