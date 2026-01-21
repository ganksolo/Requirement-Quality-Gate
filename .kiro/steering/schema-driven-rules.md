---
inclusion: always
---

# Schema-Driven Development 规则

## 核心原则

**Schema 就是法律。所有数据交互必须通过明确定义的 Pydantic Schema。**

## 1. Schema 定义规范

### 1.1 必须使用 Pydantic BaseModel

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class ExampleSchema(BaseModel):
    """Schema 必须有 docstring 说明用途"""
    
    # 必填字段：使用 ... 或 Field(...)
    required_field: str = Field(..., description="字段说明")
    
    # 可选字段：使用 Optional 或默认值
    optional_field: Optional[str] = None
    
    # 枚举字段：使用 Literal
    status: Literal["pending", "approved", "rejected"] = "pending"
    
    # 验证规则：使用 Field 的约束
    score: int = Field(..., ge=0, le=100, description="0-100分")
```

### 1.2 Schema 文件组织

所有 Schema 定义在 `src/reqgate/schemas/` 目录：

```
schemas/
├── __init__.py           # 导出所有 Schema
├── contracts.py          # 核心数据契约
├── inputs.py            # 输入层 Schema
├── outputs.py           # 输出层 Schema
├── internal.py          # 内部状态 Schema
└── config.py            # 配置 Schema
```

### 1.3 Schema 命名规范

- **输入 Schema**：`{Entity}Input` 或 `{Entity}Request`
  - 例：`RequirementPacket`, `TicketInput`
  
- **输出 Schema**：`{Entity}Output` 或 `{Entity}Response`
  - 例：`TicketScoreReport`, `ValidationResult`
  
- **内部 Schema**：`{Entity}State` 或 `{Entity}Draft`
  - 例：`AgentState`, `PRD_Draft`

## 2. 数据契约层级

### 2.1 输入层 (Input Layer)

**职责**：标准化外部输入，进行基础验证

```python
class RequirementPacket(BaseModel):
    """标准化的需求输入包"""
    raw_text: str = Field(..., min_length=10, description="清洗后的需求文本")
    source_type: Literal["Jira_Ticket", "PRD_Doc", "Meeting_Transcript"]
    project_key: str = Field(..., pattern=r"^[A-Z]{2,5}$")
    priority: Literal["P0", "P1", "P2"] = "P1"
    attachments: List[HttpUrl] = []
    
    @validator("raw_text")
    def validate_text_length(cls, v):
        if len(v) < 10:
            raise ValueError("Input too short")
        return v
```

**规则**：
- 输入层 Schema 必须包含所有必要的验证逻辑
- 不合法的输入在此层直接拒绝，不进入业务逻辑
- 使用 `@validator` 进行复杂验证

### 2.2 中间层 (Intermediate Layer)

**职责**：表示处理过程中的中间状态

```python
class PRD_Draft(BaseModel):
    """结构化的 PRD 草稿（Structuring Agent 产出）"""
    title: str = Field(..., description="动词开头的描述性标题")
    user_story: str = Field(..., description="As a X, I want Y, So that Z")
    acceptance_criteria: List[str] = Field(..., min_items=1)
    edge_cases: List[str] = []
    resources: List[str] = []
    
    # Agent 自我诊断
    missing_info: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
```

**规则**：
- 中间层 Schema 可以包含 `missing_info` 等元数据
- 允许部分字段为空（表示待补充）
- 必须可序列化为 JSON

### 2.3 输出层 (Output Layer)

**职责**：定义最终返回给用户的数据格式

```python
class ReviewIssue(BaseModel):
    """单个评审问题"""
    severity: Literal["BLOCKER", "WARNING"]
    category: Literal["MISSING_AC", "AMBIGUITY", "LOGIC_GAP", "SECURITY"]
    description: str
    suggestion: str

class TicketScoreReport(BaseModel):
    """最终评分报告"""
    total_score: int = Field(..., ge=0, le=100)
    ready_for_review: bool
    dimension_scores: dict[str, int]
    blocking_issues: List[ReviewIssue]
    non_blocking_issues: List[ReviewIssue]
    summary_markdown: str
```

**规则**：
- 输出层 Schema 必须完整（所有字段都有值）
- 必须包含人类可读的摘要字段
- 必须可直接序列化为 API Response

### 2.4 状态层 (State Layer)

**职责**：LangGraph 工作流的状态总线

```python
from typing import TypedDict

class AgentState(TypedDict):
    """LangGraph 状态总线"""
    # 输入
    packet: RequirementPacket
    
    # 中间产物
    structured_prd: Optional[PRD_Draft]
    score_report: Optional[TicketScoreReport]
    
    # 流程控制
    retry_count: int
    error_logs: List[str]
    current_stage: str
```

**规则**：
- 使用 `TypedDict` 定义 LangGraph State
- 所有节点只读写 State，不直接调用其他节点
- State 必须包含流程控制字段

## 3. Schema 验证规则

### 3.1 输入验证 (Input Validation)

**在 Schema 层进行验证，不在业务逻辑中验证**

```python
from pydantic import validator, root_validator

class TicketInput(BaseModel):
    title: str
    description: str
    ticket_type: Literal["Feature", "Bug"]
    
    @validator("title")
    def title_must_be_descriptive(cls, v):
        if len(v) < 5:
            raise ValueError("Title too short")
        if v.lower().startswith(("fix", "update", "change")):
            raise ValueError("Title must be descriptive, not action-based")
        return v
    
    @root_validator
    def check_bug_has_reproduction(cls, values):
        if values.get("ticket_type") == "Bug":
            if "reproduction" not in values.get("description", "").lower():
                raise ValueError("Bug ticket must include reproduction steps")
        return values
```

### 3.2 输出验证 (Output Validation)

**确保 Agent 输出符合 Schema**

```python
def scoring_agent_node(state: AgentState) -> AgentState:
    """评分 Agent 节点"""
    # LLM 调用
    llm_output = llm.invoke(prompt)
    
    # 强制验证输出
    try:
        report = TicketScoreReport.model_validate_json(llm_output)
    except ValidationError as e:
        # 记录错误并重试
        state["error_logs"].append(f"Schema validation failed: {e}")
        state["retry_count"] += 1
        if state["retry_count"] > 3:
            raise
        return state
    
    state["score_report"] = report
    return state
```

## 4. Schema 演化规则

### 4.1 版本控制

当 Schema 需要修改时：

1. **向后兼容的修改**（允许）：
   - 添加新的可选字段
   - 放宽验证规则
   - 添加新的枚举值

2. **破坏性修改**（需要版本升级）：
   - 删除字段
   - 修改字段类型
   - 收紧验证规则
   - 重命名字段

### 4.2 版本化 Schema

```python
# schemas/v1/contracts.py
class TicketScoreReportV1(BaseModel):
    total_score: int
    ready_for_review: bool

# schemas/v2/contracts.py
class TicketScoreReportV2(BaseModel):
    total_score: int
    ready_for_review: bool
    dimension_scores: dict[str, int]  # 新增字段
    
    @classmethod
    def from_v1(cls, v1: TicketScoreReportV1):
        """从 V1 升级到 V2"""
        return cls(
            total_score=v1.total_score,
            ready_for_review=v1.ready_for_review,
            dimension_scores={}  # 默认值
        )
```

## 5. Schema 测试规则

### 5.1 必须测试的场景

每个 Schema 必须有测试覆盖：

```python
def test_requirement_packet_valid():
    """测试合法输入"""
    packet = RequirementPacket(
        raw_text="This is a valid requirement",
        source_type="Jira_Ticket",
        project_key="PAY",
        priority="P1"
    )
    assert packet.raw_text == "This is a valid requirement"

def test_requirement_packet_invalid_text_too_short():
    """测试输入过短"""
    with pytest.raises(ValidationError):
        RequirementPacket(
            raw_text="short",  # < 10 字符
            source_type="Jira_Ticket",
            project_key="PAY"
        )

def test_requirement_packet_invalid_project_key():
    """测试非法项目 key"""
    with pytest.raises(ValidationError):
        RequirementPacket(
            raw_text="Valid requirement text",
            source_type="Jira_Ticket",
            project_key="invalid_key"  # 不符合 pattern
        )
```

### 5.2 边界测试

```python
def test_score_report_boundary_values():
    """测试边界值"""
    # 最小值
    report = TicketScoreReport(
        total_score=0,  # 边界
        ready_for_review=False,
        dimension_scores={},
        blocking_issues=[],
        non_blocking_issues=[],
        summary_markdown=""
    )
    
    # 最大值
    report = TicketScoreReport(
        total_score=100,  # 边界
        ready_for_review=True,
        dimension_scores={"completeness": 100},
        blocking_issues=[],
        non_blocking_issues=[],
        summary_markdown="Perfect"
    )
    
    # 超出边界应该失败
    with pytest.raises(ValidationError):
        TicketScoreReport(total_score=101, ...)  # > 100
```

## 6. Schema 文档规范

### 6.1 必须包含的文档

每个 Schema 必须有：

```python
class TicketScoreReport(BaseModel):
    """
    Ticket 评分报告
    
    这是 Scoring Agent 的输出，也是 Hard Gate 的输入。
    
    Attributes:
        total_score: 综合得分 (0-100)
        ready_for_review: 是否通过门禁
        dimension_scores: 各维度得分 {'completeness': 80, 'logic': 60}
        blocking_issues: 阻塞性问题列表（导致拒绝）
        non_blocking_issues: 非阻塞性问题列表（优化建议）
        summary_markdown: 给 PM 看的 Markdown 格式总结
    
    Example:
        >>> report = TicketScoreReport(
        ...     total_score=75,
        ...     ready_for_review=True,
        ...     dimension_scores={"completeness": 80, "logic": 70},
        ...     blocking_issues=[],
        ...     non_blocking_issues=[],
        ...     summary_markdown="Good quality"
        ... )
    """
    total_score: int = Field(..., ge=0, le=100, description="综合得分")
    # ... 其他字段
```

### 6.2 生成 Schema 文档

使用工具自动生成文档：

```bash
# 生成 JSON Schema
python -c "from src.reqgate.schemas.contracts import TicketScoreReport; print(TicketScoreReport.model_json_schema())"

# 生成 Markdown 文档
python scripts/generate_schema_docs.py
```

## 7. 禁止事项

### ❌ 不允许的做法

1. **不要使用 dict 传递数据**
   ```python
   # ❌ 错误
   def process(data: dict) -> dict:
       return {"score": data["score"] + 10}
   
   # ✅ 正确
   def process(input: ScoreInput) -> ScoreOutput:
       return ScoreOutput(score=input.score + 10)
   ```

2. **不要在业务逻辑中验证数据**
   ```python
   # ❌ 错误
   def scoring_logic(ticket: dict):
       if "title" not in ticket:
           raise ValueError("Missing title")
       # ...
   
   # ✅ 正确
   def scoring_logic(ticket: TicketInput):
       # Schema 已经保证 title 存在
       # ...
   ```

3. **不要返回未定义的字段**
   ```python
   # ❌ 错误
   return {"score": 80, "extra_field": "value"}  # extra_field 未定义
   
   # ✅ 正确
   return TicketScoreReport(score=80, ...)  # 所有字段都定义
   ```

## 8. 快速检查清单

在提交代码前，确保：

- [ ] 所有数据交互都使用 Pydantic Schema
- [ ] Schema 有完整的类型注解
- [ ] Schema 有 docstring 和字段描述
- [ ] 添加了必要的验证规则
- [ ] 编写了 Schema 测试（合法/非法/边界）
- [ ] 更新了 `schemas/__init__.py` 导出
- [ ] 生成了 Schema 文档

---

**记住：Schema 是契约，契约必须严格执行。**
