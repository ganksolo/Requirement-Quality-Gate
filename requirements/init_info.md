你现在只做“初始化项目骨架”，不要实现任何业务逻辑（不做 Agent、不做 Graph 节点、不做评分规则、不做 Jira/n8n 集成）。

项目：
- 名称：reqgate
- 类型：可运行的 HTTP Web Service
- Python：3.14
- 框架：FastAPI + Pydantic（含 pydantic-settings）+ LangGraph（只安装依赖，占位，不写逻辑）
- 运行：uvicorn
- 测试：pytest
- 质量：ruff（lint/format），mypy（可先宽松）
- 包管理：uv（优先）。如果无法使用 uv，则用 poetry（任选其一，不要两套）

强约束：
- 所有配置来自环境变量
- 本地用 .env（禁止提交），必须提供 .env.example
- 提供完整 .gitignore
- 必须支持本地开发与未来容器化（提供 Dockerfile 占位即可）

生成目录结构（语义必须一致）：
reqgate/
  src/reqgate/
    app/main.py                 # FastAPI app + /health（仅返回 {"status":"ok"}）
    api/routes.py               # Router 占位（不实现业务）
    config/settings.py          # Pydantic Settings，从 env 读取（最小可用）
    workflow/graph.py           # LangGraph 占位（不实现）
    agents/registry.py          # 占位
    schemas/contracts.py        # 占位
    gates/rules.py              # 占位
    adapters/llm.py             # 占位
    observability/logging.py    # 占位（可只放函数/注释）
    __init__.py
  tests/test_health.py          # pytest：请求 /health 断言 200
  docs/architecture.md          # 占位
  docs/workflow.md              # 占位
  docs/decisions.md             # 占位
  .env.example                  # 至少包含：REQGATE_ENV, REQGATE_PORT, LOG_LEVEL, OPENAI_API_KEY, GEMINI_API_KEY（空值）
  .gitignore                    # 忽略 .env、.venv、__pycache__、dist、缓存、IDE 文件
  pyproject.toml                # 依赖与工具配置（必须）
  README.md                     # 简述项目、如何运行（uvicorn）、如何测试（pytest），说明当前仅骨架
  Dockerfile                    # 占位可构建（不必完善）

要求：
- 项目必须能：安装依赖→启动→访问 GET /health→pytest 通过
- 不要创建任何业务 API（例如 /workflow/run 等），只允许 /health
- 输出最终文件树与本地运行命令
