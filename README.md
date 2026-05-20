# Health Keeper Agent for PicoClaw

This repository contains the implementation of a course homework project: a Telegram AI assistant built with PicoClaw and a custom backend service.

The homework asks for a working Telegram assistant, a useful skill, workspace files such as `SOUL.md`, `AGENT.md`, `USER.md`, and an example PicoClaw configuration. This project follows the same goal, but uses a larger structure because the selected assistant skill requires persistent state, scheduled jobs, MCP tools/resources/prompts, and Telegram reminders.

The assistant is called **Health Keeper**. It helps the user keep a lightweight health observation journal: tracking topics, scheduled questions, reminders, pending feedback, and important observations. It is not a medical diagnosis system.

## Why this repository is larger than the minimal homework template

The minimal homework submission structure is roughly:

```text
report.md
SOUL.md
AGENT.md
USER.md
Modelfile
config.json
```

This project implements a real backend around the agent instead of keeping the skill only inside prompt files. The repository therefore includes:

```text
src/                  # backend source code
picoclaw_workspace/   # PicoClaw workspace files and skills
picoclaw.example/     # sanitized PicoClaw config/security examples
scripts/              # helper scripts used during development and provider checks
docs/                 # backend and architecture documentation
logs/                 # runtime logs
data/                 # local SQLite database for development
report/               # report files and real dialog examples
```

The final submission can still be assembled according to the homework requirements, but the repository itself keeps the full implementation so the architecture and experiments remain reproducible.

## Project structure

### `src/health_agent/`

Main Python source code for the Health Keeper backend.

The code follows a layered structure:

```text
domain/       # entities and value objects
application/  # ports, services, use cases, DTOs
adapters/     # FastAPI, MCP, persistence, Telegram sender, scheduler client
bootstrap/    # dependency wiring and container setup
core/         # settings and logging
entrypoints/  # runnable API and MCP entrypoints
```

The backend is intentionally separated from PicoClaw workspace files. PicoClaw is the agent runtime, while `src/health_agent` contains the application that actually stores state, schedules jobs, and sends Telegram messages.

For detailed backend design notes, see `docs/`.

### `picoclaw_workspace/`

This is the active PicoClaw workspace used by the agent.

It contains:

```text
AGENT.md
SOUL.md
USER.md
TOOLS.md
skills/
```

The workspace defines the agent persona, behavior, tool policy, user-context policy, and reusable skills. The `skills/` directory contains workflow-level instructions such as profile bootstrap, tracking setup, recurring questions, reminders, pending feedback, and observations.

This directory may also contain PicoClaw runtime state while the agent is running. Runtime/session files should not be included in the final submission archive.

### `picoclaw.example/`

Sanitized PicoClaw examples live here.

Use this directory for safe examples of:

```text
config.json
.security.yml
```

Real API keys, Telegram bot tokens, and local private config files must not be committed or submitted.

The real PicoClaw configuration normally lives outside the repository, for example:

```text
~/.picoclaw/config.json
~/.picoclaw/.security.yml
```

### `scripts/`

Helper scripts used during development.

This directory contains small scripts for checking model providers and running the MCP server wrapper. These scripts are useful for reproducing experiments, but they are not the main application logic.

### `docs/`

Project documentation.

Use this directory for architecture notes, domain model descriptions, scheduler design, MCP design, adapter-layer documentation, and future V2 ideas. The README intentionally does not duplicate all backend documentation.

### `data/`

Local development data.

The project uses SQLite for the homework MVP. The database file is stored here during local runs. It should be treated as runtime data and should not be included in public submissions if it contains personal identifiers or health-related text.

### `report/`

Report materials.

This directory contains real dialog examples and the final `report.md`. The final report explains the implementation, experiments, limitations, and demonstrated workflows.

### `logs/`

Runtime logs may be created locally while testing the backend and MCP server.

Raw logs can contain Telegram identifiers, backend IDs, and user-provided health text. They should be sanitized before being shown in the final report.

## Runtime architecture

The project uses two cooperating runtime processes:

```text
PicoClaw Telegram gateway
  -> cloud/local LLM
  -> MCP server
  -> Health Keeper application use cases
  -> SQLite

FastAPI scheduler backend
  -> APScheduler
  -> runtime schedule execution
  -> feedback item creation
  -> Telegram message sender
```

The MCP server exposes tools, resources, and prompts to the agent. The FastAPI backend owns scheduled execution and Telegram reminder delivery.

This separation is intentional. The MCP server is started and stopped by PicoClaw, while scheduled jobs should be handled by a longer-lived backend process.

## Requirements

- Python 3.13+
- `uv`
- SQLite
- PicoClaw
- Telegram bot token
- FastAPI / Uvicorn
- APScheduler
- MCP Python package
- A model provider compatible with PicoClaw/OpenAI-style tool calling

During development, several providers were tested through small scripts. The working demo uses an API/cloud model with structured tool calls.

Install Python dependencies:

```bash
uv sync
```

## Configuration

### Environment variables

The backend needs environment variables for database and Telegram delivery. A typical local setup is:

```bash
export DATABASE_URL="sqlite+aiosqlite:///./data/health_agent.db"
export TELEGRAM_BOT_TOKEN="PASTE_TELEGRAM_BOT_TOKEN_HERE"
export SCHEDULER_CONTROL_BASE_PORT="8000"
```

Do not commit real tokens.

### PicoClaw configuration

The real PicoClaw config is normally stored outside the repository:

```text
~/.picoclaw/config.json
```

It should point to the project workspace:

```json
{
  "agents": {
    "defaults": {
      "workspace": "<abs path to the project>/picoclaw_workspace"
    }
  },
  "mcp": {
      "servers": {
        "health-agent": {
          "enabled": true,
          "command": "<abs path to the project>/scripts/run-health-mcp.sh"
        }
      }
}
```

Use the sanitized examples in `picoclaw.example/` as references.

### Secrets

Telegram tokens and model provider API keys must be stored in PicoClaw security config or environment variables, not in the repository.

Do not submit:

```text
.security.yml
.env
config.json with real API keys
database files with personal data
raw logs with Telegram IDs
```

## Running locally

Use two terminals.

### 1. Start the FastAPI backend with scheduler

From the repository root:

```bash
uv run health-api
```

The backend starts the FastAPI app and APScheduler runtime.

### 2. Start PicoClaw gateway

In another terminal:

```bash
picoclaw gateway
```

PicoClaw should:

1. read the configured workspace;
2. start the Telegram channel;
3. start the Health Keeper MCP server;
4. expose MCP tools/resources/prompts to the agent.

## Manual MCP check

The MCP server can also be checked manually:

```bash
uv run python -m health-mcp
```

A stdio MCP process may look idle after start. That is normal: it waits for MCP client messages.

For easier PicoClaw subprocess startup, the repository also contains a wrapper script in `scripts/`.

For debug you can also run MCP inspector: 

```bash
uv run mcp dev src/health_agent/entrypoints/mcp.py
```

## What to look at

- To inspect backend architecture, read `docs/`.
- To inspect agent behavior, read `picoclaw_workspace/`.
- To inspect workspace skills, read `picoclaw_workspace/skills/`.
- To inspect safe PicoClaw configuration examples, read `picoclaw.example/`.
- To inspect real dialog examples and final write-up, read `report/`.
- To inspect runtime logs, read `logs/`.
- To inspect the implementation, read `src/health_agent/`.
