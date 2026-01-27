# Schema-Driven Quality-Gated Graph Workflow
## 实施白皮书 v1.0

> **定位**
> 这是一个“工程级需求质量基础设施（Quality Infrastructure）”，用于在需求进入 Tech Review 前，
> 通过 Schema + Graph + Agent 的方式完成结构化、校验与评分，形成不可绕过的质量门禁（Gate）。
>
> 本系统不是“写需求的 AI”，而是“拦截不合格需求的工程系统”。

---

## 1. 背景与问题定义

在现有研发流程中，需求质量问题主要集中在：

- PRD / Ticket 信息不完整，关键字段缺失
- 业务流程不闭环，异常与边界条件遗漏
- Tech Review 阶段被迫承担“需求 QA”职责
- Ticket 反复打回，造成 PM 与 Tech 的低效往返

这些问题**不是能力问题，而是缺乏工程化质量门禁的问题**。

---

## 2. 设计目标与边界

### 2.1 设计目标

- 在需求进入 Tech Review 前完成质量评估
- 给出明确、可执行的补全清单
- 将“是否可评审”从主观判断转为工程规则
- 支持持续演进、回放与审计

### 2.2 明确边界（非常重要）

本系统 **不会**：
- 替代 PM 做业务取舍
- 自动生成最终产品方案
- 自动生成技术实现方案
- 绕过 Tech Review

---

## 3. 总体架构

### 3.1 三层架构

```
PM / Tech（Jira / Docs）
        │
        ▼
集成与触发层（n8n / Webhook）
        │
        ▼
核心服务层（Quality Gate Service）
  - Graph Workflow
  - PRD Structuring Agent
  - Ticket Scoring Agent
  - Hard Check / Gate
        │
        ▼
基础设施（DB / Observability / Evals）
```

### 3.2 核心构成

- **1 条主 DAG（Graph Workflow）**
- **2 个 Agent**
  - PRD Structuring Agent
  - Ticket Review & Scoring Agent
- **2 类校验**
  - Hard Check（代码）
  - Soft Check（可选，LLM）

---

## 4. Graph Workflow（主 DAG）

### 4.1 DAG 职责

- 定义执行顺序
- 定义回退条件
- 定义放行条件
- 保证流程确定性

### 4.2 核心节点

1. Input Guardrail（输入安全）
2. Normalize（统一输入结构）
3. PRD Structuring Agent
4. Hard Check #1（结构完整性）
5. Ticket Review & Scoring Agent
6. Hard Check #2（质量 Gate）
7. Formatter & Output

> **Gate 的裁决永远由代码完成，LLM 不参与最终通过与否的判断。**

---

## 5. Agent 职责定义

### 5.1 PRD Structuring Agent

**职责**
- 将零散需求映射到标准 PRD 结构
- 标记缺失项
- 提出澄清问题

**禁止**
- 发明业务逻辑
- 代替 PM 决策

---

### 5.2 Ticket Review & Scoring Agent

**职责**
- 按 Rubric 打分
- 识别阻塞项与非阻塞项
- 给出是否 Ready 的建议

**禁止**
- 给出技术实现方案
- 绕过 Gate 放行需求

---

## 6. Schema 与 Rubric

### 6.1 Schema 驱动原则

- 所有关键输入/输出必须 Schema 可校验
- Schema 是系统稳定性的法律边界

### 6.2 Rubric 治理规则（重要）

- 修改权：Tech Lead / 架构委员会
- 修改前：必须在 Golden Set 上跑回归
- 修改后：记录 rubric_version 与生效日期

---

## 7. 质量门禁（Quality Gate）

### 7.1 Gate 规则示例

- blocking_issues == 0
- score_total >= 阈值
- 必填字段全部存在

### 7.2 人工兜底机制

- 连续 3 次 Reject → 触发人工协助
- 防止系统被视为“AI 霸权”

---

## 8. 部署形态

### 8.1 本地部署
- 单机运行，适合 PoC 与调试

### 8.2 局域网部署（推荐）
- 内网服务 + n8n
- 支持多团队协作

### 8.3 云端部署
- 多 BU / 多地域
- 强合规与审计

---

## 9. 实施 Roadmap（建议）

### Phase 1（最小可用）
- Ticket Review & Scoring Agent
- Hard Gate
- Jira 回写

### Phase 2
- PRD Structuring Agent
- 模板化输出

### Phase 3
- RAG 引用历史案例
- 质量趋势分析

---

## 10. 成功标准

- Tech Review 打回率显著下降
- PM 修改轮次减少
- 需求质量问题前置消化

---

## 11. 总结

> **这是一个工程系统，而不是 AI 工具。**
> 它通过流程、规则与 Agent 的组合，
> 将“需求是否合格”从经验判断，升级为可执行的工程标准。
