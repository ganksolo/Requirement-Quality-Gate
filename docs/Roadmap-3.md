# Roadmap-3

这是**【第三份：Roadmap 与重大节点规划】**。

基于前两份文档确定的架构与数据契约，这份文档将作为**施工进度表**。遵循 Sources 的建议，我们采用**“先评分（高价值），再结构化（高难度），最后集成（全流程）”**的策略，像盖大楼一样分层交付。

- -------------------------------------------------------------------------------

第三份：Roadmap 与重大节点规划 (Roadmap & Milestones)

**1. 总体施工路线图 (The Master Plan)**

我们将整个工程分为四个阶段（Phases），总周期预计为 **4-6 周**（取决于投入人力）。

| 阶段 | 建筑隐喻 | 核心目标 | 交付物 | 周期估算 |
| --- | --- | --- | --- | --- |
| **P1** | **打地基** | **Scoring MVP**：跑通“输入 -> 评分 -> 拦截”的核心闭环。 | `scoring_agent.py`, `rubric.yaml` | Week 1 |
| **P2** | **立骨架** | **Full Workflow**：接入 Structuring Agent，串联完整 DAG。 | `structuring_agent.py`, `graph.py` | Week 2 |
| **P3** | **接水电** | **Integration**：接入 n8n 与 Jira，让 PM 能用起来。 | n8n 流程文件, Jira Webhook 配置 | Week 3 |
| **P4** | **精装修** | **Ops & Tune**：建立反馈闭环，优化 Prompt，上线生产。 | 黄金测试集, 监控面板, 运维手册 | Week 4+ |
- -------------------------------------------------------------------------------

**2. 详细阶段拆解 (Detailed Execution)**

**Phase 1: 地基与核心规则 (Foundation & Scoring Core)**

**目标**：不依赖任何 UI，仅在 Python 终端中，输入一段文本，能够输出一份准确的 JSON 评分报告。

- **Step 1.1: 规则配置化 (Rule Config)**

◦ 动作：创建 `rubric.yaml`。

◦ 内容：将 Jira 最佳实践 [Source 7-21]（如“必须有 AC”、“标题必须是动词”）转化为 YAML 配置。

◦ *验收*：代码能读取 YAML 并加载到内存中。

- **Step 1.2: 实现 Scoring Agent (The Judge)**

◦ 动作：编写 `scoring_agent_node` [Source 56]。

◦ 内容：集成 LLM，注入 Pydantic Schema (`TicketScoreReport`)。

◦ *验收*：输入一个“缺少验收标准”的 Ticket，Agent 返回的 JSON 中 `blocking_issues` 不为空。

- **Step 1.3: 实现硬门禁 (The Gate)**

◦ 动作：编写 `hard_check_gate` [Source 57]。

◦ 内容：实现 `if score < 60: return REJECT` 逻辑。

**🛑 重大节点 T1 (Milestone: The First Reject)**

- **测试方式**：找一个历史被 Tech Review 打回的真实 Ticket（烂样本）。
- **成功标准**：运行脚本，系统输出 `is_ready_for_review: False`，且准确指出了打回原因。
- -------------------------------------------------------------------------------

**Phase 2: 结构化与管线串联 (Structuring & Pipeline)**

**目标**：解决“PM 不会写文档”的问题，让系统具备“化腐朽为神奇”的能力。

- **Step 2.1: 实现 Structuring Agent (The Architect)**

◦ 动作：编写 `structuring_agent_node` [Source 47]。

◦ 内容：让 LLM 将乱序文本映射到 `PRD_Draft` Schema。

◦ *难点*：处理幻觉。需在 Prompt 中强约束“Do not invent features”。

- **Step 2.2: 串联 DAG (The Pipeline)**

◦ 动作：使用 LangGraph 将 P1 和 P2 的节点串联。

◦ 逻辑：`Input -> Structuring -> Scoring -> Gate -> End`。

◦ *容错*：如果 Structuring 失败，设计 fallback 路径直接跳到 Scoring（对原始文本评分）。

**🛑 重大节点 T2 (Milestone: End-to-End Flow)**

- **测试方式**：输入一段 300 字的杂乱会议纪要。
- **成功标准**：

1. 系统生成了一份包含 `User Story` 和 `AC` 的结构化草稿。

2. Scoring Agent 基于这份草稿打出了合理的分数。

3. 整个过程无代码报错（Crash Free）。

- -------------------------------------------------------------------------------

**Phase 3: 集成与交互 (Integration & Interface)**

**目标**：把 Python 脚本变成 PM 触手可及的服务 [Source 39, 42]。

- **Step 3.1: 封装 API (Service Layer)**

◦ 动作：用 FastAPI 封装 DAG。

◦ 接口：`POST /v1/workflow/run`，接收 `RequirementPacket`。

- **Step 3.2: 搭建 n8n 流程 (Connector)**

◦ 动作：配置 n8n 监听 Jira `Issue Created` 或 `Comment /check` 事件。

◦ 逻辑：Jira Webhook -> n8n -> Python API -> n8n -> Jira Comment。

- **Step 3.3: 格式化输出 (Decorator)**

◦ 动作：编写 Markdown Formatter。

◦ 内容：将 JSON 报告转化为人类可读的评论（包含 Emoji、加粗、列表）[Source 60]。

**🛑 重大节点 T3 (Milestone: First User Interaction)**

- **测试方式**：在 Jira Sandbox 环境创建一个 Ticket，在评论区输入 `/check`。
- **成功标准**：30秒内，Robot 账号自动回复了一条格式精美的“体检报告”，且 Jira 状态流转符合预期（如被拦截）。
- -------------------------------------------------------------------------------

**Phase 4: 运营与调优 (Operations & Tuning)**

**目标**：从“能用”到“好用”，解决误判问题 [Source 41, 62]。

- **Step 4.1: 数据持久化 (Memory)**

◦ 动作：接入 Postgres。

◦ 内容：存储每一次运行的 Input, Output, Token Usage, Latency。

- **Step 4.2: 建立黄金测试集 (Golden Set)**

◦ 动作：收集 20 个“好样本”和 20 个“坏样本”。

◦ 用途：每次修改 Prompt 或规则后，必须跑通这 40 个 Case，确保准确率不下降（Regression Testing）。

- **Step 4.3: 建立反馈闭环 (Feedback Loop)**

◦ 动作：制定运营规范。PM 对误判打 `ai-disputed` 标签，Tech Lead 每周复盘。

**🛑 重大节点 T4 (Milestone: Production Ready)**

- **测试方式**：连续运行 3 天，处理 50+ 真实需求。
- **成功标准**：

1. 系统可用性 99.9%。

2. 误判率 < 10%（PM 投诉量可控）。

3. Tech Team 反馈进入评审的文档质量有明显提升。

- -------------------------------------------------------------------------------

**3. 风险控制与应对 (Risk Management)**

在“盖楼”过程中，以下风险可能导致烂尾，需提前预防：

| 风险点 | 发生阶段 | 应对策略 | 来源参考 |
| --- | --- | --- | --- |
| **规则太死板，PM 抵触** | P1/P3 | 引入“分级策略”（Tiered Config），对内部工具项目降低阈值；提供“人工强制通过”按钮。 | Source 41, 61 |
| **LLM 幻觉，乱改需求** | P2 | Structuring Agent 仅负责“填空”和“提问”，禁止其生成业务逻辑；在 Prompt 中加入 `Strict Extraction Mode`。 | Source 47, 51 |
| **接口超时 (Timeout)** | P3 | LLM 处理长文本可能超过 60s。n8n 需配置异步回调（Webhook Callback）模式，而非同步等待。 | Source 43 |
| **Token 成本爆炸** | P4 | 在 Input Guardrail 阶段拦截垃圾请求；对长文本进行 Chunking 或摘要处理；使用 GPT-3.5/Gemini Flash 处理简单任务。 | Source 41 |
- -------------------------------------------------------------------------------

这是**第三份输出**，为你规划了从 0 到 1 的完整路径。

**接下来的计划：** 建议下一份输出 **【第四份：核心 Prompts 与规则集配置】**。因为在 Phase 1 中，Prompt 和 YAML 规则写得好不好，直接决定了“地基”是否牢固。 *你需要我为你起草第一版的核心 Prompt 和 Rubric YAML 吗？*