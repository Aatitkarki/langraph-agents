# Refactoring Plan: Improve Modularity

This plan outlines the steps to refactor the `banking_agent.py` file into a more modular structure to improve maintainability and readability.

**Goals:**

- Break down the single `banking_agent.py` file into logical components.
- Organize components into a clear directory structure under `src/`.
- Improve code organization and separation of concerns.

**Steps:**

1.  **Create New Directories:**

    - `src/`: Main source directory.
    - `src/tools/`: For tool definitions.
    - `src/agents/`: For agent definitions and prompts.
    - `src/graph/`: For graph definition, state, supervisor, and worker logic.
    - `src/utils/`: For helper functions (data loading, LLM config).

2.  **Move Code:**

    - **Tools:** Move `@tool` definitions and `PythonREPL` setup into `src/tools/` (e.g., `account_tools.py`, `calculation_tools.py`, etc.). Create `src/tools/__init__.py`.
    - **Mock Data Loading:** Move `load_mock_data` and initial loading into `src/utils/data_loader.py`.
    - **LLM Configuration:** Move LLM instantiation into `src/utils/llm_config.py`.
    - **Agent State:** Move `FinancialAgentState` into `src/graph/state.py`.
    - **Supervisor Logic:** Move `create_supervisor_finance` into `src/graph/supervisor.py`.
    - **Worker Node Logic:** Move `create_worker_node_finance` into `src/graph/worker.py`.
    - **Agent System Prompt:** Move `finance_agent_system_prompt` into `src/agents/prompts.py`.
    - **Agent Definitions:** Move `create_react_agent` calls into separate files in `src/agents/` (e.g., `account_agent.py`). Create `src/agents/__init__.py`.
    - **Graph Building:** Move graph node definitions and compilation into `src/graph/builder.py`.
    - **Main Execution Logic:** Move `run_finance_query` into a new `src/main.py`. Delete `banking_agent.py`.

3.  **Update Imports:** Modify all `import` statements in new files and `streamlit_app.py` to reflect the new structure (e.g., `from src.tools.account_tools import get_account_summary`).

4.  **Update `streamlit_app.py`:** Change imports to `from src.main import run_finance_query` and `from src.utils.llm_config import OPENAI_API_KEY`.

**Proposed File Structure:**

```
.
├── .env
├── .gitignore
├── mock_data/
│   ├── account_transactions.json
│   ├── dashboard_landing.json
│   └── exchange_rates.json
├── requirements.txt
├── streamlit_app.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── account_agent.py
│   │   ├── card_agent.py
│   │   ├── exchange_rate_agent.py
│   │   ├── transaction_agent.py
│   │   └── prompts.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   ├── state.py
│   │   ├── supervisor.py
│   │   └── worker.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── account_tools.py
│   │   ├── calculation_tools.py
│   │   ├── card_tools.py
│   │   ├── exchange_tools.py
│   │   └── transaction_tools.py
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py
│       └── llm_config.py
└── PLAN.md
```

**Mermaid Diagram (High-Level Structure):**

```mermaid
graph TD
    A[streamlit_app.py] --> B(src/main.py);
    A --> S[src/utils/llm_config.py];
    B --> C{src/graph/builder.py};
    C --> D[src/graph/state.py];
    C --> E[src/graph/supervisor.py];
    C --> F[src/graph/worker.py];
    C --> G(src/agents/__init__.py);
    G --> H[src/agents/account_agent.py];
    G --> I[src/agents/transaction_agent.py];
    G --> J[src/agents/card_agent.py];
    G --> K[src/agents/exchange_rate_agent.py];
    H --> L(src/tools/__init__.py);
    I --> L;
    J --> L;
    K --> L;
    L --> M[src/tools/account_tools.py];
    L --> N[src/tools/transaction_tools.py];
    L --> O[src/tools/card_tools.py];
    L --> P[src/tools/exchange_tools.py];
    L --> Q[src/tools/calculation_tools.py];
    H --> R[src/agents/prompts.py];
    I --> R;
    J --> R;
    K --> R;
    H --> S;
    I --> S;
    J --> S;
    K --> S;
    E --> S;
    M --> T[src/utils/data_loader.py];
    N --> T;
    O --> T;
    P --> T;

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#cfc,stroke:#333,stroke-width:2px
    style L fill:#ff9,stroke:#333,stroke-width:2px
    style S fill:#fcc,stroke:#333,stroke-width:2px
    style T fill:#9cf,stroke:#333,stroke-width:2px
    style R fill:#cff,stroke:#333,stroke-width:2px
```
