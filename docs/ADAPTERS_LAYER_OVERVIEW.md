# Adapters Layer Overview

This document describes the adapter layer of the Health Agent project.

The project is intentionally larger than a minimal PicoClaw homework bot. The main reason is that the selected skill requires persistent state, scheduled execution, Telegram delivery, and a real backend boundary. The adapter layer is the place where the application is connected to concrete technologies: MCP, FastAPI, APScheduler, SQLite/SQLAlchemy, Telegram Bot API, and HTTP clients.

## 1. Architectural Role

The project follows a Clean Architecture style.

```text
external world
  -> inbound adapters
      -> application use cases
          -> domain model
          -> application ports
              -> outbound adapters
                  -> external systems / storage
```

The application layer knows only use cases, services, DTOs, and ports. It does not know PicoClaw, FastMCP, FastAPI, APScheduler, SQLAlchemy, or Telegram.

Adapters are responsible for:

- translating external requests into application use case calls;
- converting application/domain objects into transport-friendly responses;
- implementing application ports with concrete technologies;
- hiding framework-specific details from the domain and application layers.

## 2. Current Adapter Structure

```text
src/health_agent/adapters/
  inbound/
    api/
      endpoints/
        scheduler.py
      router.py

    mcp/
      server.py
      tools.py
      resources.py
      prompts.py
      context_notes.md

    scheduler_runtime.py

  outbound/
    persistence/
      relational/
        db.py
        models.py
        repositories.py
      uow.py

    scheduler_http_client.py
    telegram_message_sender.py
```

The adapter layer has two main directions:

```text
Inbound:
  MCP server
  FastAPI scheduler-control API
  APScheduler runtime callbacks

Outbound:
  SQLite / SQLAlchemy persistence
  UnitOfWork
  Scheduler HTTP client
  Telegram Bot API sender
```

## 3. Why There Are Several Inbound Adapters

The system has more than one entry point.

The user talks to the agent through Telegram and PicoClaw. PicoClaw calls the MCP server. The MCP server invokes application use cases.

Scheduled jobs are different. They are not initiated by the user directly. They are initiated by APScheduler inside the FastAPI backend process.

Therefore, there are three inbound adapters:

| Adapter | Purpose |
|---|---|
| MCP adapter | Agent-facing tools, resources, and prompts |
| FastAPI adapter | Internal scheduler-control API |
| Scheduler runtime adapter | APScheduler callbacks that execute scheduled jobs |

Keeping them separate makes lifecycle and responsibilities clearer.

## 4. MCP Inbound Adapter

Location:

```text
src/health_agent/adapters/inbound/mcp/
```

Files:

```text
server.py
tools.py
resources.py
prompts.py
context_notes.md
```

The MCP adapter is the main agent-facing boundary. It exposes the backend as MCP primitives:

```text
Tools     -> state-changing commands
Resources -> read-only backend state
Prompts   -> reusable analysis/report workflows
```

The MCP adapter does not implement business logic. It validates and translates tool/resource/prompt calls, then delegates to application use cases.

### `server.py`

`server.py` creates the FastMCP server and registers tools, resources, and prompts.

It is intentionally small. Its responsibility is composition, not business behavior.

Expected responsibilities:

- create the MCP server object;
- inject application use cases;
- register tool functions;
- register resource handlers;
- register prompt templates.

### `tools.py`

`tools.py` exposes commands that change state or trigger application actions.

Examples:

- `get_user_profile_id_by_telegram_id`;
- `create_user_profile`;
- `create_tracking_target`;
- `create_schedule_cron`;
- `create_question`;
- `create_medicine`;
- `create_reminder`;
- `answer_feedback`;
- `skip_feedback`;
- `record_observation`.

Tool functions should remain thin wrappers:

```text
MCP tool input
  -> type conversion / validation
  -> application use case
  -> compact text result for the agent
```

They should not contain domain rules. Domain behavior belongs to entities, value objects, application services, and use cases.

### `resources.py`

`resources.py` exposes read-only views of backend state.

Resources are used instead of many `list_*` tools because read operations should not pollute the tool-selection space.

Current resource families:

```text
health-agent://profile/{user_profile_id}
health-agent://tracking-targets/{user_profile_id}
health-agent://schedule-crons/{user_profile_id}
health-agent://questions/{tracking_target_id}
health-agent://medicines/{tracking_target_id}
health-agent://reminders/{medicine_id}
health-agent://pending-feedback/{user_profile_id}
health-agent://feedback-window/{user_profile_id}/{start}/{end}
health-agent://observations-window/{user_profile_id}/{start}/{end}
```

Resources should return compact state, not raw database dumps. The goal is to give the agent enough context to choose the next action.

### `prompts.py`

`prompts.py` exposes reusable prompt templates through MCP.

In this project prompts are used for higher-level analytical/reporting workflows, not for state-changing procedures. Operational procedures are represented as PicoClaw workspace skills.

Examples:

- `analyze_user_state`;
- `summarize_interaction_for_report`.

This gives a clear separation:

```text
Skills      -> operational multi-step workflows
MCP prompts -> reusable reasoning/report templates
MCP tools   -> concrete backend actions
MCP resources -> read-only state
```

## 5. FastAPI Inbound Adapter

Location:

```text
src/health_agent/adapters/inbound/api/
```

The FastAPI adapter exposes internal scheduler-control endpoints.

It is not the public user interface. Users interact through Telegram/PicoClaw. FastAPI exists because scheduler runtime needs a stable long-running backend process.

Typical endpoint responsibilities:

- register a newly created schedule with APScheduler;
- pause/resume/remove jobs;
- expose health/status endpoints if needed.

The FastAPI adapter receives HTTP calls from the MCP-side application code through `SchedulerHttpClient`.

## 6. Scheduler Runtime Adapter

Location:

```text
src/health_agent/adapters/inbound/scheduler_runtime.py
```

This adapter owns APScheduler and translates cron triggers into application use case calls.

Responsibilities:

- start APScheduler;
- shut down APScheduler cleanly;
- load active schedules on startup;
- register jobs for active `ScheduleCron` entities;
- pause/resume/remove jobs;
- call `ScheduleRuntimeUseCases.run_schedule_cron(...)` when a cron fires.

The runtime adapter should not decide what feedback items to create or what Telegram messages to send. That behavior belongs to application use cases and services.

The execution direction is:

```text
APScheduler job fires
  -> SchedulerRuntime adapter
  -> ScheduleRuntimeUseCases
  -> ScheduleExecutionService
  -> repositories + MessageSender port
```

## 7. Persistence Outbound Adapter

Location:

```text
src/health_agent/adapters/outbound/persistence/
```

Persistence uses SQLAlchemy with SQLite.

Files:

```text
relational/db.py
relational/models.py
relational/repositories.py
uow.py
```

Responsibilities:

- create the async SQLAlchemy engine;
- create session factories;
- define relational models;
- map database rows to domain entities;
- implement repository ports;
- provide transactional UnitOfWork behavior.

## 8. SQLAlchemy Models vs Domain Entities

SQLAlchemy models are infrastructure objects.

Domain entities live in:

```text
src/health_agent/domain/entities/
```

Database models live in:

```text
src/health_agent/adapters/outbound/persistence/relational/models.py
```

The repository maps between these two representations.

This is important because the domain model should not depend on SQLAlchemy. The project can later replace SQLite/SQLAlchemy without rewriting domain behavior.

## 9. Repository Adapters

Repositories implement application ports.

The project uses grouped repositories rather than one repository per database table. This keeps the adapter layer smaller while preserving clear responsibility boundaries.

Typical repository groups:

```text
UserProfileRepository
TrackingRepository
FeedbackRepository
```

A repository may work with several tables if those tables belong to one aggregate or workflow.

## 10. UnitOfWork Adapter

`SqlAlchemyUnitOfWork` implements the application `UnitOfWork` port.

Its responsibilities:

- open one SQLAlchemy session per use case call;
- provide repository instances;
- commit successful use cases;
- rollback failed use cases;
- close the session.

Use cases should explicitly commit after successful state changes.

The UnitOfWork is especially important because many agent actions create several connected entities, for example:

```text
create schedule cron
  -> save schedule in SQLite
  -> notify scheduler runtime
```

or:

```text
APScheduler fires
  -> create feedback items
  -> send Telegram message
  -> commit created items
```

## 11. Scheduler HTTP Client

Location:

```text
src/health_agent/adapters/outbound/scheduler_http_client.py
```

This adapter implements the `SchedulerControl` port.

The MCP process creates or changes schedule configuration through application use cases. The actual APScheduler runtime lives in the FastAPI process. Therefore, the MCP-side code needs an outbound client that notifies the scheduler backend.

Example flow:

```text
MCP create_schedule_cron tool
  -> ScheduleManagementUseCases
  -> SQLite commit
  -> SchedulerHttpClient
  -> POST /scheduler/jobs/{schedule_cron_id}/track
  -> FastAPI scheduler backend
  -> APScheduler registers job
```

This adapter is the bridge between the MCP subprocess lifecycle and the long-running scheduler process.

## 12. Telegram Message Sender

Location:

```text
src/health_agent/adapters/outbound/telegram_message_sender.py
```

This adapter implements the `MessageSender` port.

It sends messages through Telegram Bot API when scheduled jobs fire.

Important identity distinction:

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal backend UUID
```

For the current MVP only private Telegram chats are supported, so `telegram_user_id` and `telegram_chat_id` can be the same value. The internal `user_profile_id` must still be a backend UUID.

The Telegram adapter should not know domain rules. It receives a chat ID and a text message from the application service and sends it.

## 13. Logging Boundary

Logging is configured in the core layer and used by adapters.

The project uses separate log files for main runtimes:

```text
logs/api.log
logs/mcp.log
```

This separation makes debugging easier:

- `api.log` shows FastAPI, APScheduler, and scheduled execution;
- `mcp.log` shows MCP server activity and tool/resource/prompt calls.

Runtime logs should not be treated as public report artifacts because they may contain Telegram identifiers and health-related text. Sanitized excerpts can be used in documentation.

## 14. Adapter Design Trade-offs

The current design is intentionally more complex than a single-file homework bot.

The complexity is justified by the selected skill:

- health tracking requires persistent state;
- reminders require scheduled execution;
- pending feedback requires a database;
- Telegram delivery requires an outbound API adapter;
- the agent needs a stable MCP boundary to reach backend use cases.

The project therefore uses a small production-like architecture rather than putting all logic into prompt files or MCP tool functions.

## 15. Known Limitations

Current limitations:

- the system is optimized for private Telegram chats, not group chats;
- scheduler timezone handling is simplified and currently cron values are treated as backend/runtime cron values;
- duplicate schedule creation is possible if the model does not read existing schedule resources before creating a new one;
- the MCP server is not a full database admin panel;
- destructive operations are intentionally not exposed in the MVP;
- raw logs and database files are not suitable for submission because they can contain private identifiers.

These limitations are acceptable for the MVP and are useful targets for V2.

## 16. Summary

The adapter layer makes the Health Agent runnable.

MCP connects the agent to backend tools, resources, and prompts. FastAPI hosts scheduler-control endpoints. APScheduler executes schedule jobs. SQLAlchemy persists state in SQLite. Telegram Bot API sends scheduled messages. HTTP clients connect the MCP and scheduler processes.

The domain and application layers remain independent of these concrete technologies.
