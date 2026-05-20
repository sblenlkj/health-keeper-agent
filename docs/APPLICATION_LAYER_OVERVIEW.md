# Application Layer Overview

This document describes the application layer of the Health Agent project.

The application layer coordinates domain objects, ports, services, and use cases. It does not know about FastAPI, MCP, APScheduler, Telegram HTTP API, SQLAlchemy models, or concrete database sessions.

The main goal of this layer is to keep business scenarios explicit while avoiding infrastructure details.

## 1. Main Responsibility

The application layer answers the question:

```text
What should the system do for this user action?
```

It does not answer:

```text
How exactly is data stored?
How exactly is Telegram called?
How exactly does MCP receive the request?
How exactly does FastAPI route the request?
```

Those details belong to adapters.

## 2. Current Structure

The application layer is organized into:

```text
application/
  dto/
    agent_context.py

  ports/
    feedback_repository.py
    message_sender.py
    scheduler_control.py
    tracking_repository.py
    unit_of_work.py
    user_profile_repository.py

  services/
    agent_context_service.py
    feedback_service.py
    schedule_execution_service.py

  use_cases/
    user_profile_use_cases.py
    tracking_use_cases.py
    feedback_use_cases.py
    observation_use_cases.py
    schedule_management_use_cases.py
    schedule_runtime_use_cases.py
```

The layer has three main kinds of objects:

- use cases;
- application services;
- ports.

## 3. Use Cases

Use cases are scenario-level classes.

They are called by inbound adapters:

- MCP tools;
- FastAPI scheduler endpoints;
- APScheduler runtime.

A use case owns the transaction boundary:

```text
open UnitOfWork
  -> load data
  -> call domain/application logic
  -> save data
  -> commit
```

This means use cases are responsible for calling `commit`.

Application services do not open their own UnitOfWork and do not commit.

## 4. Why Use Cases Are Grouped

The project intentionally does not follow the “one use case = one file” style.

For this MVP, that would create too many tiny files and make navigation harder.

Instead, use cases are grouped by business area:

```text
UserProfileUseCases
TrackingUseCases
FeedbackUseCases
ObservationUseCases
ScheduleManagementUseCases
ScheduleRuntimeUseCases
```

This keeps the application layer compact and still explicit.

## 5. UserProfileUseCases

`UserProfileUseCases` coordinates technical Telegram identity and business user profile.

Typical scenarios:

- get user profile ID by Telegram user ID;
- create user profile;
- update user profile;
- get compact agent context by user profile ID.

The current MVP uses Telegram identity from workspace configuration. The agent first gets or creates a user profile and then uses `user_profile_id` for further tools.

## 6. TrackingUseCases

`TrackingUseCases` manages the configuration part of the system:

- tracking targets;
- questions;
- medicines;
- reminders.

These are not daily records. They define what the assistant should track and ask later.

Typical scenarios:

- create tracking target;
- list tracking targets;
- create question;
- list questions;
- create medicine;
- list medicines;
- create reminder;
- list reminders.

## 7. FeedbackUseCases

`FeedbackUseCases` manages routine answers.

Feedback items are concrete questions waiting for an answer, or already answered.

Typical scenarios:

- list pending feedback;
- answer feedback item;
- skip feedback item.

The feedback stream is the main routine data source of the system.

## 8. ObservationUseCases

`ObservationUseCases` manages important observations.

Observations are not routine answers. They are notable facts that should remain visible.

Typical scenarios:

- record important observation;
- list recent observations;
- list observations by time window.

## 9. Why Schedule Use Cases Are Split

Scheduling is the most important architectural split in the application layer.

The project has two runtime processes:

```text
MCP process
FastAPI scheduler process
```

The same `ScheduleCron` domain entity is used by both, but the orchestration is different.

Therefore the project separates:

```text
ScheduleManagementUseCases
ScheduleRuntimeUseCases
```

## 10. ScheduleManagementUseCases

`ScheduleManagementUseCases` is used by the MCP/API management side.

It is responsible for creating or changing schedule configuration.

It depends on:

- UnitOfWorkFactory;
- SchedulerControl port.

Typical scenarios:

- create schedule cron;
- list schedule crons for a user;
- pause schedule cron;
- resume schedule cron.

When it creates a schedule, it must notify the external scheduler runtime:

```text
create ScheduleCron in DB
  -> commit
  -> call SchedulerControl.track_schedule_cron(schedule_id)
```

This is why it depends on `SchedulerControl`.

## 11. ScheduleRuntimeUseCases

`ScheduleRuntimeUseCases` is used inside the FastAPI scheduler process.

It is responsible for executing already configured schedules.

It depends on:

- UnitOfWorkFactory;
- ScheduleExecutionService.

Typical scenarios:

- get schedule cron;
- list active schedule crons;
- run schedule cron.

It does not depend on `SchedulerControl`, because it already runs inside the scheduler runtime process. It should not call itself through HTTP.

This separation removes the need for optional scheduler-control dependencies and makes the process boundary explicit.

## 12. Application Services

Application services contain reusable application logic used by use cases.

They do not own transactions.

They either:

- contain pure logic and do not know about UnitOfWork;
- or receive an already opened UnitOfWork as a method argument.

Current services:

```text
AgentContextService
FeedbackService
ScheduleExecutionService
```

## 13. AgentContextService

`AgentContextService` builds compact LLM-facing context.

It does not return the whole database.

It returns only:

- display name;
- language;
- communication style;
- general notes;
- active tracking targets.

The agent should fetch operational details through tools when needed.

This keeps prompt context small and avoids dumping internal IDs and large database state into the model.

## 14. FeedbackService

`FeedbackService` creates and updates feedback items.

Examples:

- create feedback item from question;
- create feedback item from reminder feedback question;
- answer feedback item;
- skip feedback item.

This service does not use repositories directly. It works with domain objects.

## 15. ScheduleExecutionService

`ScheduleExecutionService` contains the reusable logic for what happens when a schedule fires.

It loads:

- the schedule;
- user profile;
- Telegram user/chat;
- questions linked to the schedule;
- reminders linked to the schedule.

Then it:

- creates feedback items from questions;
- sends reminder messages;
- creates feedback items from reminder feedback questions;
- delegates message sending through `MessageSender`.

It is called only by `ScheduleRuntimeUseCases`.

## 16. Ports

Ports are interfaces that the application layer depends on.

Current ports:

```text
UserProfileRepository
TrackingRepository
FeedbackRepository
UnitOfWork
MessageSender
SchedulerControl
```

The application layer depends on ports, not concrete implementations.

Concrete implementations live in adapters.

## 17. UnitOfWork

`UnitOfWork` groups repositories and transaction control.

It exposes:

- `users`;
- `tracking`;
- `feedback`;
- `commit`;
- `rollback`.

The project uses `UnitOfWorkFactory` so each use case call gets a fresh UnitOfWork and a fresh database session.

This avoids sharing SQLAlchemy sessions between MCP calls, FastAPI requests, and scheduler jobs.

## 18. Transaction Rule

The project follows this rule:

```text
UseCase owns UoW.
Service uses UoW.
Repository lives inside UoW.
Adapter creates UseCase calls.
```

This prevents accidental nested transactions and keeps commit/rollback behavior predictable.

## 19. Application Layer Summary

The application layer is the orchestration core of the project.

It connects domain meaning with external adapters without depending on concrete infrastructure.

The most important design choice is the split between:

```text
ScheduleManagementUseCases
ScheduleRuntimeUseCases
```

because schedule creation happens in the MCP-facing process, while schedule execution happens in the FastAPI scheduler process.
