# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Edict 2.0 is an AI multi-agent collaboration framework inspired by the ancient Chinese "Three Provinces and Six Ministries" (三省六部) governance system. It implements institutionalized AI agent collaboration with mandatory review gates and structured workflows.

**Key Repositories:**
- 2.0 Maintained: `https://github.com/N1nEmAn/edict-2.0`
- Original: `https://github.com/cft0808/edict`

## Common Commands

### Installation
```bash
# Source install (recommended for 2.0)
chmod +x install.sh && ./install.sh

# Docker quick start
docker run -p 7891:7891 cft0808/edict
```

### Development
```bash
# Frontend dev mode (hot reload)
cd edict/frontend && npm run dev  # http://localhost:5173

# Build frontend
cd edict/frontend && npm run build && cd ../..

# Start data refresh loop
bash scripts/run_loop.sh

# Start dashboard server (legacy)
python3 dashboard/server.py  # http://127.0.0.1:7891
```

### Testing
```bash
# Python syntax check
python3 -m py_compile dashboard/server.py
python3 -m py_compile scripts/kanban_update.py

# Frontend type check + build
cd edict/frontend && npx tsc -b && npm run build && cd ../..

# E2E kanban tests (9 scenarios)
python3 tests/test_e2e_kanban.py
```

## Architecture

### Three Provinces Flow (主链路)
```
User → Taizi(太子/分拣) → Zhongshu(中书/起草) → Menxia(门下/审议) → Shangshu(尚书/派发)
                                    ↑                     |
                                    └─── 封驳(rejection) ─┘
                                                              ↓
                                            Six Ministries (并行执行)
                                                              ↓
                                                         Summary → User
```

**Critical Rules:**
- Menxia review is mandatory, cannot be skipped
- Zhongshu cannot directly command ministries
- Ministries cannot bypass Shangshu to report to Zhongshu
- Maximum 3 review rounds, forced approval on 3rd round

### Task State Machine
States: `Taizi → Zhongshu → Menxia → Assigned → Doing → Review → Done`
Also: `Blocked`, `Cancelled`, `Pending`

### Agent Permission Matrix
- `taizi` can call: `zhongshu`
- `zhongshu` can call: `menxia`, `shangshu`
- `menxia` can call: `shangshu`, `zhongshu` (for rejection)
- `shangshu` can call: `libu`, `hubu`, `bingbu`, `xingbu`, `gongbu`, `libu_hr`
- Six ministries cannot call other agents

### Technology Stack
- **Backend (New):** FastAPI, SQLAlchemy async, Pydantic
- **Backend (Legacy):** Python stdlib HTTP server (`dashboard/server.py`)
- **Event Bus:** Redis Streams
- **Database:** PostgreSQL + JSONB
- **Frontend:** React 18, TypeScript, Vite, Zustand, TailwindCSS
- **AI Runtime:** OpenClaw Gateway

## Key Directories

```
agents/           # 12 Agent SOUL.md personality templates
dashboard/        # Legacy dashboard server (Python stdlib)
edict/
  backend/        # FastAPI backend (new architecture)
  frontend/       # React 18 + TypeScript + Vite
  migration/      # Database migration tools
scripts/          # CLI tools (kanban_update.py, refresh_live_data.py)
tests/            # E2E tests
docs/             # Architecture documentation
```

## Agent Definitions

Agents are defined in `agents/<name>/SOUL.md`. Each agent has:
- Role description and personality
- Allowed downstream agents (permission matrix)
- Task handling instructions
- Output format requirements

The 12 agents are: `taizi`, `zhongshu`, `menxia`, `shangshu`, `bingbu`, `gongbu`, `hubu`, `libu`, `libu_hr`, `xingbu`, `zaochao`, and `agents.json` orchestration config.

## Task Data Model

Tasks contain:
- `state`: Current state in the flow
- `org`: Current responsible organization (省/部)
- `flow_log`: State transitions with timestamps
- `progress_log`: Agent activities and todos
- `todos`: Checklist items with status
- `_scheduler`: Stall detection and retry config

## Historical Alignment

This project maps Sui-Tang dynasty governance (隋创唐成) to AI collaboration:
- Three Provinces: Sequential decision chain, not parallel
- Six Ministries: Parallel execution layer under Shangshu
- 封驳 (Fengbo): Rejection mechanism returning to Zhongshu

Reference: 《隋书·百官志》, 《旧唐书·职官志》, 《新唐书·百官志》
