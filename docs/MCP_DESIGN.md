# MCP Design

This document describes how the Health Agent project uses MCP as the boundary between PicoClaw/OpenClaw and the Health Agent backend.

The project is not a simple prompt-only Telegram bot. It uses MCP to expose a real backend with persistent state, scheduled jobs, reminders, feedback items, observations, and read-only state resources.

## 1. Purpose of MCP in This Project

MCP is the agent-facing API.

The agent should not keep important health state only in Telegram history or LLM context. Instead, it should use MCP to interact with persistent backend state.

```text
Telegram user
  -> PicoClaw gateway
      -> LLM
          -> MCP tools/resources/prompts
              -> application use cases
                  -> SQLite database
                  -> FastAPI scheduler backend
                  -> Telegram Bot API
```

MCP is used to preserve and operate on:

- user profiles;
- tracking targets;
- schedule crons;
- recurring questions;
- medicines/supplements/creams/procedures;
- reminders;
- pending feedback items;
- answered feedback history;
- observations.

## 2. MCP Primitive Separation

The project follows a strict MCP design rule:

```text
Tools     -> actions and state changes
Resources -> read-only state
Prompts   -> reusable reasoning/report workflows
Skills    -> operational multi-step procedures in the PicoClaw workspace
```

This separation is important for model reliability.

A tool call should do something. A resource should show state. A prompt should provide a reusable analytical template. A skill should describe how to combine tools/resources for a workflow.

## 3. Why the MCP Server Is Not a Database Admin Panel

The MCP server intentionally exposes only the operations needed for the MVP workflow.

It is not a complete CRUD API. It does not expose every table or every possible update operation.

This is intentional because too many tools make the model worse at tool selection and increase baseline context.

The MVP loop is:

```text
bootstrap profile
  -> create tracking target
  -> create schedule/question/reminder
  -> wait for scheduler
  -> create pending feedback
  -> answer or skip feedback
  -> record observations
  -> read state through resources
  -> analyze state through prompts
```

Operations not exposed in MVP include:

- hard deletion;
- arbitrary edits of all fields;
- bulk updates;
- full database export;
- admin database inspection;
- DayCard generation;
- advanced analytics;
- automatic snapshot rebuilding.

Some deployments may expose activate/deactivate operations. Deactivation is preferred over deletion because historical health data should remain available for debugging and later analysis.

## 4. Identity Model

The system uses three different IDs.

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal backend UUID
```

Rules:

- `telegram_user_id` is not `user_profile_id`;
- `telegram_chat_id` is not `user_profile_id`;
- all domain operations use `user_profile_id`;
- Telegram IDs are used only for bootstrap and delivery;
- for private Telegram chats, `telegram_user_id == telegram_chat_id`;
- the agent must never invent UUIDs.

The bootstrap flow is:

```text
Telegram direct chat / user-provided Telegram ID
  -> get_user_profile_id_by_telegram_id
      -> existing user_profile_id
      OR
      -> create_user_profile
```

Once resolved, the internal `user_profile_id` should be kept in session memory if available. If session memory is unreliable, the agent should state the `user_profile_id` in chat so it remains visible in conversation history.

## 5. Current Tools

Tools are commands. They change state or trigger backend operations.

### 5.1 User/Profile Tools

#### `get_user_profile_id_by_telegram_id`

Looks up the internal profile UUID by Telegram user ID.

Input:

```text
telegram_user_id
```

Output:

```text
FOUND user_profile_id=...
```

or a soft not-found response.

This tool should not be treated as a fatal error when the user does not exist yet. "Not found" is a normal bootstrap branch.

#### `create_user_profile`

Creates a new internal user profile.

Input:

```text
telegram_user_id
telegram_chat_id
username optional
display_name optional
language
timezone
communication_style optional
general_notes optional
```

Output:

```text
OK. Created user_profile_id=...
```

The tool should be used only when lookup says the profile does not exist.

### 5.2 Tracking Target Tool

#### `create_tracking_target`

Creates a long-lived topic to observe.

Input:

```text
user_profile_id
title
code
description optional
```

Examples:

- leg pain;
- stomach pain;
- digestion;
- headache;
- sleep;
- general wellbeing.

A tracking target is the root object for related questions, medicines/procedures, reminders, feedback, and observations.

### 5.3 Schedule Tool

#### `create_schedule_cron`

Creates a shared cron schedule.

Input:

```text
user_profile_id
title
cron
description optional
```

Example:

```text
0 11 * * *  -> every day at 11:00 according to backend cron interpretation
```

After creating a schedule, the application notifies the FastAPI scheduler backend so APScheduler can register the job.

A known MVP limitation is that the agent may create a duplicate schedule if it does not read `health-agent://schedule-crons/{user_profile_id}` first. A future improvement is to add a dedicated `get_or_create_schedule_cron` tool.

### 5.4 Question Tool

#### `create_question`

Creates a reusable scheduled question template.

Input:

```text
tracking_target_id
schedule_cron_id
text
```

A question is not the user's answer. It is a template used by the scheduler to create pending feedback items when the cron fires.

### 5.5 Medicine Tool

#### `create_medicine`

Creates a medicine-like item related to a tracking target.

Input:

```text
tracking_target_id
title
kind
description optional
```

In this MVP, `medicine` is a broad term. It may mean:

- medicine;
- supplement;
- cream;
- ointment;
- procedure;
- routine.

The agent must not prescribe or recommend treatment. It only records/reminds what the user requested.

### 5.6 Reminder Tool

#### `create_reminder`

Creates a reminder connected to a medicine-like item and a schedule.

Input:

```text
medicine_id
schedule_cron_id
message
feedback_question optional
```

If `feedback_question` is provided, the scheduler can create a pending feedback item for the user to answer.

### 5.7 Feedback Tools

#### `answer_feedback`

Answers a pending feedback item.

Input:

```text
feedback_item_id
answer
```

Use this when the user gives a routine answer to a scheduled question or reminder feedback question.

#### `skip_feedback`

Skips a pending feedback item.

Use this when the user explicitly says they do not want to answer or forgot the answer.

### 5.8 Observation Tool

#### `record_observation`

Records an important notable fact.

Input:

```text
user_profile_id
title
description
```

Use observations for notable events, not routine daily answers.

Examples:

- mild pain in left foot after waking up;
- strong stomach pain after a specific meal;
- unusual reaction after taking a supplement;
- symptom improved or worsened in a meaningful way.

Routine answers should be stored through feedback, not observations.

## 6. Current Resources

Resources are read-only views of backend state.

Read operations are represented as resources instead of tools to reduce the number of tool choices and keep tool selection focused on actions.

### 6.1 Profile Resource

```text
health-agent://profile/{user_profile_id}
```

Returns compact user profile context and active tracking targets.

This is the primary read-only entry point after bootstrap.

### 6.2 Tracking Targets Resource

```text
health-agent://tracking-targets/{user_profile_id}
```

Returns active tracking targets.

Use it before creating a new tracking target or when the user asks what is being tracked.

### 6.3 Schedule Crons Resource

```text
health-agent://schedule-crons/{user_profile_id}
```

Returns active schedule crons.

Use it before creating questions or reminders when the user asks to reuse an existing time.

### 6.4 Questions Resource

```text
health-agent://questions/{tracking_target_id}
```

Returns active question templates for a tracking target.

### 6.5 Medicines Resource

```text
health-agent://medicines/{tracking_target_id}
```

Returns active medicines, supplements, creams, procedures, or routines connected to a tracking target.

### 6.6 Reminders Resource

```text
health-agent://reminders/{medicine_id}
```

Returns active reminders for a medicine-like item.

### 6.7 Pending Feedback Resource

```text
health-agent://pending-feedback/{user_profile_id}
```

Returns unanswered feedback items.

Use it when the user asks what needs to be answered or when the user gives a short answer that should be matched to a pending item.

### 6.8 Feedback Window Resource

```text
health-agent://feedback-window/{user_profile_id}/{start}/{end}
```

Returns feedback items created in a time window.

Prefer date-only values:

```text
health-agent://feedback-window/{user_profile_id}/2026-05-17/2026-05-18
```

### 6.9 Observations Window Resource

```text
health-agent://observations-window/{user_profile_id}/{start}/{end}
```

Returns observations recorded in a time window.

Prefer date-only values:

```text
health-agent://observations-window/{user_profile_id}/2026-05-17/2026-05-18
```

## 7. Current Prompts

Prompts are reusable reasoning/report templates exposed by the MCP server.

The project keeps prompts for higher-level workflows where the server provides a standardized analysis template.

### `analyze_user_state`

Use when the user asks for analysis or a state summary.

Expected workflow:

1. ensure the current `user_profile_id`;
2. read the profile resource;
3. read tracking targets if needed;
4. inspect pending feedback if relevant;
5. inspect feedback and observation windows if the user asks about history;
6. summarize recorded facts, possible patterns, unclear points, and next tracking suggestions;
7. avoid diagnosis and treatment instructions;
8. do not write state unless the user reports a new important fact or explicitly asks to remember it.

### `summarize_interaction_for_report`

Use when preparing technical report material.

Expected workflow:

1. summarize the user's goal;
2. list the tools/resources/prompts used;
3. describe backend effects;
4. mention persistence and scheduler behavior;
5. list limitations and possible improvements;
6. avoid exposing secrets or private identifiers unless sanitized.

## 8. Skills vs MCP Prompts

The project also uses PicoClaw workspace skills.

The split is:

```text
Skills:
  operational procedures

MCP prompts:
  analysis/report templates
```

Examples of skills:

- bootstrap user profile;
- setup tracking target;
- setup recurring question;
- setup medicine reminder;
- review pending feedback;
- answer or skip feedback;
- record important observation;
- analyze known state.

There is some overlap between prompts and skills. This is acceptable for the homework because it demonstrates both mechanisms. In a production version, the boundary could be simplified.

## 9. Scheduler Design Through MCP

MCP creates schedule configuration, but it does not execute schedules.

Execution is handled by the FastAPI backend with APScheduler.

Creation flow:

```text
Agent
  -> create_schedule_cron MCP tool
  -> ScheduleManagementUseCases
  -> SQLite
  -> SchedulerControl port
  -> SchedulerHttpClient
  -> FastAPI scheduler endpoint
  -> APScheduler registers job
```

Execution flow:

```text
APScheduler fires
  -> SchedulerRuntime adapter
  -> ScheduleRuntimeUseCases
  -> ScheduleExecutionService
  -> create pending feedback
  -> send Telegram reminder/question
  -> persist results
```

This separation is necessary because the MCP server usually lives as a subprocess controlled by PicoClaw, while the scheduler must be a stable long-running runtime.

## 10. Tool-Calling Runtime Experience

The project was tested with local and cloud models.

Key findings:

- some local 7B/8B models return JSON text instead of real structured tool calls;
- Groq free-tier TPM limits were too small for a rich workspace context;
- Ollama Cloud `gpt-oss:20b-cloud` successfully returned structured OpenAI-compatible tool calls;
- a rich agent workspace with skills increases baseline context usage;
- for production, a multi-agent setup with smaller per-agent skill context would be more efficient.

This is not a failure of MCP. It is a practical context-engineering trade-off.

## 11. Known Limitations

Current MCP limitations:

- duplicate schedule creation can happen if the agent does not read schedule resources first;
- there is no `get_or_create_schedule_cron` tool yet;
- there are no generic update tools;
- destructive delete operations are intentionally absent;
- group chats are not supported in the MVP;
- identity extraction depends on PicoClaw session metadata or user-provided Telegram ID;
- resources are useful but not always selected by the model before creation.

These limitations are documented and are suitable V2 improvements.

## 12. Future Improvements

Possible V2 MCP improvements:

- `get_or_create_schedule_cron`;
- `get_or_create_tracking_target`;
- safer update tools;
- explicit lookup tools for schedules and targets;
- admin/debug resources available only in development mode;
- DayCard resources;
- DayTargetSummary resources;
- export resources;
- web search tool;
- model-specific compressed tool descriptions;
- multi-agent decomposition: profile agent, tracking agent, scheduler agent, feedback agent, analysis agent.

## 13. Summary

The MCP layer is the operational bridge between the LLM agent and the Health Agent backend.

Tools perform actions, resources expose state, prompts standardize analysis/report workflows, and PicoClaw skills describe operational procedures. The design keeps business logic in the application/domain layers and keeps the MCP server as a thin agent-facing adapter.
