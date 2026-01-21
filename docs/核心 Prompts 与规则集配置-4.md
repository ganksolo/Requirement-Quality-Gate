# 核心 Prompts 与规则集配置-4

这是**【第四份：核心 Prompts 与规则集配置】**。这份文档是系统的**“灵魂”**。代码骨架（Python）只是躯壳，而 Prompt 和 YAML 配置决定了 Agent 是像一个“只会废话的 AI”还是一个“严格的 Tech Lead”。遵循 Source 的版本化策略，我们将这些定义为 **v1.0 版本**。--------------------------------------------------------------------------------第四份：核心 Prompts 与规则集配置 (Core Prompts & Rule Sets)**1. 规则集配置 (`scoring_rubric.yaml`)**这是系统的**“宪法”**。我们不把规则写死在 Prompt 里，而是抽离为配置文件，以便针对 Feature、Bug 或不同敏感度（Tier）进行动态调整。设计依据：• **Feature**: 依据 Jira 最佳实践，侧重 AC 和 User Story [Source 7-21]。• **Bug**: 侧重复现步骤 [Source 27]。

`# scoring_rubric.yaml (v1.0)

# ==========================================
# 场景 A: 新功能开发 (Feature / User Story)
# ==========================================
FEATURE:
  threshold: 60  # 及格线
  
  # 权重分配 (总和 1.0)
  weights:
    completeness: 0.4      # 完整性 (AC, Story, UI)
    logic_closure: 0.3     # 逻辑闭环 (Flow, State)
    clarity: 0.2           # 清晰度 (No ambiguous words)
    dependencies: 0.1      # 依赖 (API, Resources)

  # 必填字段检查 (Missing -> Blocker)
  required_fields:
    - field: "acceptance_criteria"
      error_msg: "缺失验收标准 (Acceptance Criteria)。必须定义 'Given/When/Then' 或明确的验证列表。"
    - field: "user_story"
      error_msg: "缺失用户故事 (User Story)。必须说明 'As a <User>, I want <Action>, So that <Value>'。"

  # 负面清单 (出现即扣分/拦截)
  negative_patterns:
    - pattern: "优化体验"
      severity: "BLOCKER"
      reason: "模糊词汇。请定义具体的优化指标（如：响应时间 < 1s）。"
    - pattern: "TBD"
      severity: "WARNING"
      reason: "包含待定内容 (TBD)。请确认是否影响开发估时。"

# ==========================================
# 场景 B: 缺陷修复 (Bug Fix)
# ==========================================
BUG:
  threshold: 50
  
  weights:
    reproduction: 0.5      # 复现步骤最重要
    expected_behavior: 0.3 # 期望结果
    environment: 0.2       # 环境信息
    
  required_fields:
    - field: "steps_to_reproduce"
      error_msg: "缺失复现步骤。请列出 1, 2, 3 步骤。"
    - field: "environment"
      error_msg: "缺失环境信息 (OS/Browser/AppVersion)。"

# ==========================================
# 敏感度分级 (Tier Overrides)
# ==========================================
TIERS:
  TIER_1_CRITICAL:  # 支付、安全、核心链路
    threshold: 80
    extra_required: ["security_impact", "rollback_plan"]
    
  TIER_3_INTERNAL:  # 内部工具
    threshold: 40
    ignore_blockers: ["user_story"] # 内部工具可以不写 User Story`
--------------------------------------------------------------------------------**2. Agent #1: 结构化 Agent Prompt (`prompt_structuring.md`)定位**：资深产品经理助理。 **任务**：将非结构化输入（录音/草稿）映射到标准 PRD 结构 [Source 40, 47]。 **核心约束**：只提取，不编造（No Hallucination）。

`# Role
You are an expert Product Manager Assistant. Your goal is to structure raw requirement inputs into a standardized PRD JSON format.

# Input Data
Raw Text: {raw_text}
Source Type: {source_type} (e.g., Meeting Transcript, Jira Ticket Draft)

# Output Schema (JSON)
You must strictly follow the `PRD_Draft` JSON schema provided in the function definition.

# Extraction Rules (The Constitution)
1. **User Story**: Extract who the user is, what they want, and why. If not explicitly stated, try to infer reasonably from context, but mark confidence as "low".
2. **Acceptance Criteria (AC)**: Look for specific conditions that denote completion (Given/When/Then). 
   - CRITICAL: If no AC is found, DO NOT invent one. Leave it empty and add a question to `clarification_questions`.
3. **Edge Cases**: Extract any mentions of error states, empty states, or failure paths.
4. **Resources**: Extract any URLs (Figma, Docs) mentioned in the text.

# Handling Missing Information
- You are a **Structure Mapper**, not a Writer. 
- If a critical section (like `Acceptance Criteria`) is missing in the source text:
  1. Leave the field empty or null.
  2. Add a specific entry to `missing_info` list.
  3. Generate a `clarification_question` asking the PM to provide it.

# Negative Constraints
- Do not output markdown text. Output ONLY valid JSON.
- Do not assume business logic that isn't in the text. (e.g., if logic for "VIP users" is not mentioned, do not add it).`
--------------------------------------------------------------------------------**3. Agent #2: 评分 Agent Prompt (`prompt_scoring.md`)定位**：严格、情绪稳定的 Tech Lead [Source 41]。 **任务**：根据 `scoring_rubric.yaml` 对 Ticket 进行评分。

`# Role
You are a strict Tech Lead and Gatekeeper for the engineering team. 
Your job is to review the following Ticket/PRD and decide if it is **Ready for Development**.

# Context & Configuration
- Scenario: {scenario_name} (e.g., FEATURE, BUG)
- Sensitivity Tier: {tier_name}
- Pass Threshold: {threshold} points

# Input Ticket
Title: {ticket_title}
Description: {ticket_description}
Acceptance Criteria: {ticket_ac}

# Scoring Rubric (Weights)
{weights_json}

# Blocking Rules (The Hard Gate)
You must mark an issue as **BLOCKER** (severity="BLOCKER") if:
1. **Missing Required Fields**: The ticket is missing {required_fields}.
2. **Ambiguity**: The ticket uses vague words like "optimize", "better", "fix" without quantitative metrics. [Ref: Jira Best Practice #3]
3. **Logic Gaps**: The user flow is incomplete (e.g., A -> ? -> C).
4. **Tier Specific**: If Tier is CRITICAL, missing "Security Impact" is a BLOCKER.

# Output Format (JSON)
Produce a `TicketScoreReport` JSON with:
1. `total_score`: 0-100.
2. `dimension_scores`: Breakdown based on weights.
3. `blocking_issues`: List of fatal errors (violating Blocking Rules).
4. `non_blocking_issues`: Suggestions for improvement (e.g., better formatting).
5. `summary_comment`: A concise, constructive summary for the Product Manager.

# Tone Guidelines
- Be objective and direct.
- Do not be overly polite. If it's bad, say it's bad and explain why.
- Provide actionable advice (e.g., "Add a screenshot" instead of "Clarify UI").

# Example Analysis (Few-Shot)
Input: "Title: Search Box. Desc: Make it better."
Output:
{
  "total_score": 20,
  "blocking_issues": [
    {"type": "BLOCKER", "category": "AMBIGUITY", "description": "'Make it better' is not actionable.", "suggestion": "Define specific metrics (e.g., <200ms response)."},
    {"type": "BLOCKER", "category": "MISSING_AC", "description": "No Acceptance Criteria found.", "suggestion": "List at least 3 scenarios (Happy path, No results, Error)."}
  ]
}`
--------------------------------------------------------------------------------**4. 实施指南：如何组装 (Assembly Instructions)**有了以上三个文件，在 Python 代码中（Phase 1 阶段）你需要这样组装：**4.1 动态加载配置**在 `scoring_agent_node` 中，不要写死 Prompt，而是读取 YAML 并动态填槽：

`import yaml

# 1. 加载配置
with open("scoring_rubric.yaml") as f:
    rubric_config = yaml.safe_load(f)

def build_scoring_prompt(ticket):
    # 2. 判断场景 (简单逻辑)
    scenario = "BUG" if ticket.type == "Bug" else "FEATURE"
    config = rubric_config[scenario]
    
    # 3. 填充 Prompt 模板
    prompt_template = open("prompt_scoring.md").read()
    final_prompt = prompt_template.format(
        scenario_name=scenario,
        tier_name="TIER_2_STANDARD", # 后续可根据 Project 动态获取
        threshold=config['threshold'],
        ticket_title=ticket.title,
        ticket_description=ticket.description,
        ticket_ac=ticket.acceptance_criteria or "N/A",
        weights_json=str(config['weights']),
        required_fields=str(config['required_fields'])
    )
    return final_prompt`
**4.2 验证 Prompt 效果 (Evals)**在正式上线前，请使用以下两个 Case 测试 `prompt_scoring.md` 的效果：1. **Case A (烂需求)**：    ◦ *Input*: Title="导出功能", Desc="加个导出按钮"    ◦ *Expected*: Score < 40, 触发 `MISSING_AC` 和 `AMBIGUITY` 两个 Blocker。2. **Case B (好需求)**：    ◦ *Input*: (使用 Source 中的 Template 填写的一个完整需求)    ◦ *Expected*: Score > 80, 无 Blocker。--------------------------------------------------------------------------------这是**第四份输出**。你现在拥有了：1. **宏观蓝图** (Architecture)2. **微观契约** (Schema & Coupling)3. **施工计划** (Roadmap)4. **核心配置与Prompts** (Rule Sets)至此，**构建这个系统的所有理论准备和核心资产已经齐备**。你可以直接把这四份文档交给开发人员（或你自己）开始 Phase 1 的编码工作。**建议：** 在正式 coding 前，是否需要我为你提供一份 **Phase 1 的 main.py 最小可执行代码**？这样你可以直接复制粘贴运行，验证这个 Prompt 和 Config 是否如预期工作。

NotebookLM 提供的内容未必准确，因此请仔细核查回答内容。