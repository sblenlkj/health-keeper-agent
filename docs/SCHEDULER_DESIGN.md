# Scheduler Design

The project uses a separate FastAPI backend with APScheduler.

The MCP server does not execute scheduled jobs. It only exposes tools for the agent.

## Why scheduler is not inside MCP

An MCP stdio server is usually launched by the agent runtime as a subprocess.

This makes it a poor place for long-running scheduled jobs, because its lifecycle may depend on the client. If the MCP server is restarted, in-memory scheduler state is lost.

For this reason, the MVP keeps scheduled execution in the FastAPI backend.

## Runtime structure

```text
OpenClaw / PicoClaw
  -> MCP server
      -> tools
      -> application use cases
      -> SQLite database
      -> scheduler control HTTP client

FastAPI backend
  -> APScheduler runtime
  -> scheduler control endpoints
  -> schedule runtime use cases
  -> Telegram message sender
```

## Schedule creation flow

When the agent creates a schedule:

1. MCP tool calls `ScheduleManagementUseCases`.
2. Use case saves `ScheduleCron` into SQLite.
3. Use case calls `SchedulerControlClient`.
4. HTTP client calls FastAPI scheduler endpoint.
5. FastAPI scheduler runtime registers the cron job in APScheduler.

## Schedule execution flow

When APScheduler fires:

1. Scheduler runtime calls `ScheduleRuntimeUseCases`.
2. Runtime use case loads questions and reminders for the schedule.
3. Questions create feedback items.
4. Reminders send Telegram messages.
5. Reminder feedback questions also create feedback items.
6. Changes are committed to SQLite.

## Why cron

The MVP stores schedules as cron expressions.

This is simple, explicit, and easy to integrate with APScheduler.

The project intentionally does not implement user-local abstractions like “morning”, “evening”, or flexible routines in the first version. User timezone exists in the profile, but schedule execution is stored and processed in UTC.

## V2 ideas

Future improvements:

- dedicated scheduler worker process;
- richer schedule lifecycle;
- activity history for tracking targets;
- local-day-aware summaries;
- DayCard and DayTargetSummary;
- automatic reload of all active schedules after database changes;
- better admin endpoints for debugging scheduler state.
