# Phase 1: Foundation & Scoring Core - Design

## Architecture Overview

Phase 1 采用分层架构，确保关注点分离和可测试性。

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (FastAPI App + Health Endpoint)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Configuration Layer             │
│  (Settings + Environment Variables)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Schema Layer                    │
│  (Pydantic Models - Data Contracts)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Business Logic Layer            │
│  ┌─────────────────────────────────┐   │
│  │  Scoring Agent                  │   │
│  │  (LLM + Rubric + Prompt)        │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Hard Gate                      │   │
│  │  (Decision Logic)               │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│  (LLM Adapter + Config Loader)          │
└─────────────────────────────────────────┘
```

## Component Design

### 1. Application Layer

#### 1.1 FastAPI Application

**文件**: `src/reqgate/app/main.py`

**职责**:
- 创建 FastAPI 应用实例
- 注册路由
- 配置中间件
- 生命周期管理

**接口**:
```python
from fastapi import FastAPI
from src.reqgate.config.settings import get_settings

def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()
    
    app = FastAPI(
        title="ReqGate API",
        version="0.1.0",
        description="Requirement Quality Gate System"
    )
    
    # 注册路由
    from src.reqgate.api.routes import router
    app.include_router(router)
    
    return app

app = create_app()
```

#### 1.2 Health Endpoint

**文件**: `src/reqgate/api/routes.py`

**接口**:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}
```

### 2. Configuration Layer

#### 2.1 Settings

**文件**: `src/reqgate/config/settings.py`

**职责**:
- 从环境变量读取配置
- 提供类型安全的配置访问
- 验证配置合法性

**Schema**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    reqgate_env: Literal["development", "staging", "production"] = "development"
    reqgate_port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # LLM 配置
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_timeout: int = 30
    
    gemini_api_key: str = ""  # 可选
    gemini_model: str = "gemini-pro"
    
    # 评分配置
    rubric_file_path: str = "config/scoring_rubric.yaml"
    default_threshold: int = 60
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# 单例模式
_settings: Settings | None = None

def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### 3. Schema Layer

#### 3.1 Input Schema

**文件**: `src/reqgate/schemas/inputs.py`

```python
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Literal, List

class RequirementPacket(BaseModel):
    """
    标准化的需求输入包
    
    这是系统的输入契约，所有外部输入必须转化为此格式。
    """
    
    raw_text: str = Field(
        ...,
        min_length=10,
        description="清洗后的纯文本需求描述"
    )
    
    source_type: Literal["Jira_Ticket", "PRD_Doc", "Meeting_Transcript"] = Field(
        ...,
        description="输入来源类型"
    )
    
    project_key: str = Field(
        ...,
        pattern=r"^[A-Z]{2,5}$",
        description="项目标识，如 'PAY', 'OPS'"
    )
    
    priority: Literal["P0", "P1", "P2"] = Field(
        default="P1",
        description="优先级"
    )
    
    ticket_type: Literal["Feature", "Bug"] = Field(
        default="Feature",
        description="需求类型"
    )
    
    attachments: List[HttpUrl] = Field(
        default_factory=list,
        description="附件链接列表"
    )
    
    @validator("raw_text")
    def validate_text_not_empty(cls, v: str) -> str:
        """验证文本不为空或仅包含空白"""
        if not v.strip():
            raise ValueError("raw_text cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_text": "实现用户登录功能，支持邮箱和手机号登录",
                "source_type": "Jira_Ticket",
                "project_key": "AUTH",
                "priority": "P1",
                "ticket_type": "Feature"
            }
        }
```

#### 3.2 Output Schema

**文件**: `src/reqgate/schemas/outputs.py`

```python
from pydantic import BaseModel, Field
from typing import Literal, List

class ReviewIssue(BaseModel):
    """单个评审问题"""
    
    severity: Literal["BLOCKER", "WARNING"] = Field(
        ...,
        description="问题严重程度"
    )
    
    category: Literal[
        "MISSING_AC",
        "AMBIGUITY",
        "LOGIC_GAP",
        "SECURITY",
        "MISSING_FIELD"
    ] = Field(
        ...,
        description="问题分类"
    )
    
    description: str = Field(
        ...,
        description="问题描述"
    )
    
    suggestion: str = Field(
        ...,
        description="修改建议"
    )

class TicketScoreReport(BaseModel):
    """
    Ticket 评分报告
    
    这是 Scoring Agent 的输出，也是 Hard Gate 的输入。
    """
    
    total_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="综合得分 (0-100)"
    )
    
    ready_for_review: bool = Field(
        ...,
        description="是否通过门禁"
    )
    
    dimension_scores: dict[str, int] = Field(
        ...,
        description="各维度得分，如 {'completeness': 80, 'logic': 60}"
    )
    
    blocking_issues: List[ReviewIssue] = Field(
        default_factory=list,
        description="阻塞性问题列表（导致拒绝）"
    )
    
    non_blocking_issues: List[ReviewIssue] = Field(
        default_factory=list,
        description="非阻塞性问题列表（优化建议）"
    )
    
    summary_markdown: str = Field(
        ...,
        description="给 PM 看的 Markdown 格式总结"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_score": 45,
                "ready_for_review": False,
                "dimension_scores": {
                    "completeness": 40,
                    "logic": 50
                },
                "blocking_issues": [
                    {
                        "severity": "BLOCKER",
                        "category": "MISSING_AC",
                        "description": "缺少验收标准",
                        "suggestion": "请添加至少 3 条 Given/When/Then 格式的验收标准"
                    }
                ],
                "non_blocking_issues": [],
                "summary_markdown": "## 评分结果\n\n总分: 45/100 ❌\n\n### 阻塞性问题\n- 缺少验收标准"
            }
        }
```

#### 3.3 State Schema

**文件**: `src/reqgate/schemas/internal.py`

```python
from typing import TypedDict, Optional, List
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport

class AgentState(TypedDict):
    """
    Agent 工作流状态
    
    Phase 1 暂时不使用 LangGraph，但预留状态定义。
    """
    
    # 输入
    packet: RequirementPacket
    
    # 输出
    score_report: Optional[TicketScoreReport]
    
    # 流程控制
    retry_count: int
    error_logs: List[str]
    current_stage: str
```

### 4. Business Logic Layer

#### 4.1 Rubric Configuration

**文件**: `config/scoring_rubric.yaml`

```yaml
# 评分规则配置 v1.0

FEATURE:
  threshold: 60
  
  weights:
    completeness: 0.4
    logic_closure: 0.3
    clarity: 0.2
    dependencies: 0.1
  
  required_fields:
    - field: "acceptance_criteria"
      error_msg: "缺失验收标准 (Acceptance Criteria)。必须定义 'Given/When/Then' 或明确的验证列表。"
    - field: "user_story"
      error_msg: "缺失用户故事 (User Story)。必须说明 'As a <User>, I want <Action>, So that <Value>'。"
  
  negative_patterns:
    - pattern: "优化体验"
      severity: "BLOCKER"
      reason: "模糊词汇。请定义具体的优化指标（如：响应时间 < 1s）。"
    - pattern: "TBD"
      severity: "WARNING"
      reason: "包含待定内容 (TBD)。请确认是否影响开发估时。"

BUG:
  threshold: 50
  
  weights:
    reproduction: 0.5
    expected_behavior: 0.3
    environment: 0.2
  
  required_fields:
    - field: "steps_to_reproduce"
      error_msg: "缺失复现步骤。请列出 1, 2, 3 步骤。"
    - field: "environment"
      error_msg: "缺失环境信息 (OS/Browser/AppVersion)。"
```

#### 4.2 Rubric Loader

**文件**: `src/reqgate/gates/rules.py`

```python
import yaml
from pathlib import Path
from typing import Dict, Any
from src.reqgate.config.settings import get_settings

class RubricLoader:
    """评分规则加载器"""
    
    def __init__(self):
        self._cache: Dict[str, Any] | None = None
    
    def load(self) -> Dict[str, Any]:
        """加载评分规则"""
        if self._cache is not None:
            return self._cache
        
        settings = get_settings()
        rubric_path = Path(settings.rubric_file_path)
        
        if not rubric_path.exists():
            raise FileNotFoundError(f"Rubric file not found: {rubric_path}")
        
        with open(rubric_path, "r", encoding="utf-8") as f:
            self._cache = yaml.safe_load(f)
        
        return self._cache
    
    def get_scenario_config(self, ticket_type: str) -> Dict[str, Any]:
        """获取特定场景的配置"""
        rubric = self.load()
        scenario = "BUG" if ticket_type == "Bug" else "FEATURE"
        
        if scenario not in rubric:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        return rubric[scenario]

# 单例
_rubric_loader: RubricLoader | None = None

def get_rubric_loader() -> RubricLoader:
    """获取规则加载器单例"""
    global _rubric_loader
    if _rubric_loader is None:
        _rubric_loader = RubricLoader()
    return _rubric_loader
```

#### 4.3 Scoring Agent

**文件**: `src/reqgate/agents/scoring.py`

```python
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.adapters.llm import get_llm_client
from src.reqgate.gates.rules import get_rubric_loader
from typing import Dict, Any

class ScoringAgent:
    """评分 Agent"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.rubric_loader = get_rubric_loader()
    
    def score(self, packet: RequirementPacket) -> TicketScoreReport:
        """
        对需求进行评分
        
        Args:
            packet: 标准化的需求输入
        
        Returns:
            评分报告
        """
        # 1. 加载规则
        config = self.rubric_loader.get_scenario_config(packet.ticket_type)
        
        # 2. 构建 Prompt
        prompt = self._build_prompt(packet, config)
        
        # 3. 调用 LLM
        llm_response = self.llm.invoke(
            prompt=prompt,
            response_schema=TicketScoreReport
        )
        
        # 4. 解析并验证输出
        report = TicketScoreReport.model_validate_json(llm_response)
        
        return report
    
    def _build_prompt(self, packet: RequirementPacket, config: Dict[str, Any]) -> str:
        """构建评分 Prompt"""
        prompt_template = """# Role
You are a strict Tech Lead and Gatekeeper for the engineering team.
Your job is to review the following Ticket/PRD and decide if it is **Ready for Development**.

# Context & Configuration
- Scenario: {scenario}
- Pass Threshold: {threshold} points
- Weights: {weights}

# Input Ticket
Type: {ticket_type}
Project: {project_key}
Priority: {priority}
Content:
{raw_text}

# Scoring Rubric
Required Fields: {required_fields}
Negative Patterns: {negative_patterns}

# Blocking Rules
You must mark an issue as **BLOCKER** if:
1. Missing any required field
2. Contains ambiguous words without quantitative metrics
3. Logic flow is incomplete

# Output Format
Produce a JSON matching the TicketScoreReport schema with:
- total_score: 0-100
- dimension_scores: breakdown by weights
- blocking_issues: fatal errors
- non_blocking_issues: suggestions
- summary_markdown: concise summary for PM

Be objective and direct. Provide actionable advice.
"""
        
        scenario = "BUG" if packet.ticket_type == "Bug" else "FEATURE"
        
        return prompt_template.format(
            scenario=scenario,
            threshold=config["threshold"],
            weights=config["weights"],
            ticket_type=packet.ticket_type,
            project_key=packet.project_key,
            priority=packet.priority,
            raw_text=packet.raw_text,
            required_fields=config.get("required_fields", []),
            negative_patterns=config.get("negative_patterns", [])
        )
```

#### 4.4 Hard Gate

**文件**: `src/reqgate/gates/decision.py`

```python
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.gates.rules import get_rubric_loader
from typing import Literal

GateDecision = Literal["PASS", "REJECT"]

class HardGate:
    """硬性门禁"""
    
    def __init__(self):
        self.rubric_loader = get_rubric_loader()
    
    def decide(
        self,
        report: TicketScoreReport,
        ticket_type: str
    ) -> GateDecision:
        """
        执行门禁决策
        
        Args:
            report: 评分报告
            ticket_type: 需求类型
        
        Returns:
            PASS 或 REJECT
        """
        config = self.rubric_loader.get_scenario_config(ticket_type)
        threshold = config["threshold"]
        
        # 规则 1: 存在任何 BLOCKER 级问题，直接拒绝
        if len(report.blocking_issues) > 0:
            return "REJECT"
        
        # 规则 2: 分数低于阈值，拒绝
        if report.total_score < threshold:
            return "REJECT"
        
        return "PASS"
```

### 5. Infrastructure Layer

#### 5.1 LLM Adapter

**文件**: `src/reqgate/adapters/llm.py`

```python
from abc import ABC, abstractmethod
from typing import Type, Any
from pydantic import BaseModel
from src.reqgate.config.settings import get_settings
import openai
import json

class LLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    @abstractmethod
    def invoke(self, prompt: str, response_schema: Type[BaseModel]) -> str:
        """调用 LLM 并返回 JSON 字符串"""
        pass

class OpenAIClient(LLMClient):
    """OpenAI 客户端实现"""
    
    def __init__(self):
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout
    
    def invoke(self, prompt: str, response_schema: Type[BaseModel]) -> str:
        """调用 OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical requirement reviewer."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
        
        except openai.APITimeoutError as e:
            raise TimeoutError(f"LLM request timeout: {e}")
        except openai.APIError as e:
            raise RuntimeError(f"LLM API error: {e}")

# 单例
_llm_client: LLMClient | None = None

def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAIClient()
    return _llm_client
```

## Data Flow

### Scoring Flow

```
RequirementPacket
      ↓
[Rubric Loader] → Load Config
      ↓
[Scoring Agent] → Build Prompt → Call LLM → Parse JSON
      ↓
TicketScoreReport
      ↓
[Hard Gate] → Check Blockers → Check Score
      ↓
GateDecision (PASS/REJECT)
```

## Error Handling

### Error Types

1. **Validation Error** (Schema 层)
   - 输入不符合 Schema
   - 处理: 返回 400 错误

2. **LLM Timeout** (Infrastructure 层)
   - LLM 调用超时
   - 处理: 重试 1 次，失败后返回 503

3. **LLM API Error** (Infrastructure 层)
   - API Key 无效、配额不足等
   - 处理: 记录日志，返回 500

4. **Config Error** (Configuration 层)
   - 配置文件缺失或格式错误
   - 处理: 启动时检查，失败则拒绝启动

## Testing Strategy

### Unit Tests

1. **Schema Tests** (`tests/test_schemas.py`)
   - 测试合法输入
   - 测试非法输入
   - 测试边界值

2. **Rubric Loader Tests** (`tests/test_rules.py`)
   - 测试 YAML 加载
   - 测试场景配置获取
   - 测试缓存机制

3. **Scoring Agent Tests** (`tests/test_scoring_agent.py`)
   - Mock LLM 调用
   - 测试 Prompt 构建
   - 测试输出解析

4. **Hard Gate Tests** (`tests/test_hard_gate.py`)
   - 测试拦截逻辑
   - 测试边界条件

### Integration Tests

1. **End-to-End Test** (`tests/test_integration.py`)
   - 真实 LLM 调用（可选，需要 API Key）
   - 完整流程测试

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-xxx

# Optional
REQGATE_ENV=development
REQGATE_PORT=8000
LOG_LEVEL=INFO
OPENAI_MODEL=gpt-4o
OPENAI_TIMEOUT=30
RUBRIC_FILE_PATH=config/scoring_rubric.yaml
DEFAULT_THRESHOLD=60
```

## Deployment

Phase 1 仅本地开发，不涉及部署。

## Performance Considerations

- LLM 调用是性能瓶颈（20-30s）
- Schema 验证非常快（< 10ms）
- 配置加载使用缓存

## Security Considerations

- API Key 通过环境变量管理
- 输入验证在 Schema 层
- 不记录敏感信息到日志

## Future Enhancements (Phase 2+)

- 添加 Structuring Agent
- 集成 LangGraph 工作流
- 添加 Input Guardrail
- 支持异步处理
