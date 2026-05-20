# Domain Model Overview

This document describes the current domain model of the project and the boundaries of the first MVP version.

The goal is to keep the first version small, understandable, and useful. More advanced ideas are intentionally moved to V2.

## 1. Main Domain Idea

The system is a personal observation assistant.

It helps a user:

- define what they want to observe;
- configure recurring questions;
- configure medicine or routine reminders;
- collect answers as feedback;
- record important observations separately;
- later provide this context to an AI agent.

The MVP does not try to build a full medical system, diagnostic system, daily analytics engine, or complex health timeline. It focuses on reliable data collection.

## 2. Core Domain Flow

The current domain flow is:

```text
User
  -> UserProfile
       -> TrackingTarget
            -> Question
            -> Medicine
                 -> Reminder

       -> ScheduleCron
            -> Question
            -> Reminder

       -> FeedbackItem
       -> Observation
```

The key idea is separation between:

- configuration: what should be tracked and asked;
- routine feedback: answers to regular questions;
- important observations: notable events or changes reported by the user or created by the agent.

## 3. Entities in MVP

### User

`User` is a technical identity connected to Telegram.

It stores Telegram-related identifiers and minimal display information.

Typical fields:

- internal UUID;
- Telegram user ID;
- Telegram chat ID;
- Telegram username or display name.

`User` should stay technical. Business logic should not depend directly on it.

### UserProfile

`UserProfile` is the business profile of the user.

It stores settings that affect assistant behavior.

Typical fields:

- user ID;
- language;
- timezone;
- active/inactive state;
- communication style;
- general notes.

Most business entities should be connected to `UserProfile`, not directly to `User`.

The profile timezone is important because user-facing time and day boundaries may depend on it. Internal timestamps are still stored in UTC.

### TrackingTarget

`TrackingTarget` describes a real user observation topic.

Examples:

- digestion;
- leg pain;
- joint pain;
- headache;
- general wellbeing.

A tracking target is not a diagnosis. It is simply a topic the user wants to observe.

Typical fields:

- user profile ID;
- title;
- description;
- code;
- active/inactive flag.

A tracking target can have related questions and medicines.

### Question

`Question` is a reusable question template.

It belongs to a tracking target and is connected to a schedule cron.

Examples:

- “What did you eat today?”
- “Was there any stomach discomfort?”
- “How did your legs feel today?”

A question is not a feedback answer itself. It is a template used to create feedback items.

Typical fields:

- tracking target ID;
- schedule cron ID;
- text;
- active/inactive flag.

### Medicine

`Medicine` represents something the user takes, applies, or does in relation to a tracking target.

The name is used broadly. It may include:

- medicine;
- supplement;
- cream;
- ointment;
- procedure;
- routine action.

Typical fields:

- tracking target ID;
- title;
- description;
- kind;
- active/inactive flag.

### Reminder

`Reminder` is a reusable reminder template connected to a medicine and a schedule cron.

It contains the message that should be sent to the user.

It may also contain a feedback question that will create a feedback item after the reminder.

Example:

```text
message: "Remember to take magnesium after food."
feedback_question: "Did you take magnesium? If yes, what dose and when?"
```

Typical fields:

- medicine ID;
- schedule cron ID;
- message;
- optional feedback question;
- active/inactive flag.

### ScheduleCron

`ScheduleCron` is a shared cron slot.

It allows several questions and reminders to share one scheduled trigger.

This prevents the system from sending many small messages at nearly the same time.

Example:

```text
Evening slot: 0 21 * * *
```

At this cron time, the system can collect all active questions and reminders linked to the schedule and create/send them together.

Typical fields:

- user profile ID;
- title;
- cron expression;
- active/inactive flag.

### FeedbackItem

`FeedbackItem` is a concrete question waiting for the user's answer, or already answered.

It can be created from:

- a regular `Question`;
- a `Reminder` feedback question.

For MVP, a feedback item does not need to store the source question or source reminder. The important thing is that the user was asked something and may answer it.

Typical fields:

- user profile ID;
- text;
- answer;
- status;
- created at;
- answered at.

The feedback stream is the main source of routine daily information.

Examples:

- what the user ate;
- whether the user took medicine;
- whether the user applied cream;
- whether the user had symptoms;
- how the user felt today.

### Observation

`Observation` is an important observation recorded by the user or agent.

It is reserved for notable facts, not routine answers.

Examples:

- “Morning diarrhea.”
- “Strong leg pain after walking.”
- “Unusual reaction after magnesium.”
- “Stomach pain started in the evening.”

Routine daily data should go into `FeedbackItem`. Important, notable facts should go into `Observation`.

Typical fields:

- user profile ID;
- title or label;
- description;
- recorded at;
- optional occurred at.

## 4. Data Collection Philosophy

The MVP distinguishes two types of collected information.

### Routine feedback

Routine feedback is stored in `FeedbackItem`.

This includes everyday answers:

- food;
- medicine intake;
- cream application;
- general check-in answers;
- regular symptom questions.

This prevents the observation log from becoming noisy.

### Important observations

Important observations are stored in `Observation`.

These are created less often and should remain visible.

The agent may create an observation when the user reports something significant.

## 5. What MVP Does Not Do

The first version intentionally does not include:

- DayCard;
- DayTargetSummary;
- AgentContextSnapshot;
- daily automatic summaries;
- target activity history;
- complex status history;
- automatic synchronization between feedback, observations, and day summaries;
- technical tracking targets;
- strict medical event taxonomy;
- complex event payloads;
- diagnosis logic.

These ideas are valuable, but they would make the first version too large.

## 6. V2 Ideas

### DayCard

`DayCard` may represent a user's local day as a UTC interval.

It can later be used to group feedback items and observations by the user's local date.

This is useful because the user may live in different timezones, while the system stores timestamps in UTC.

Possible fields:

- user profile ID;
- local date;
- timezone snapshot;
- UTC start;
- UTC end;
- optional summary.

### DayTargetSummary

`DayTargetSummary` may store an agent-generated summary for one tracking target inside one day.

This would allow the system to summarize separately:

- digestion;
- leg pain;
- joint pain;
- headache;
- other active targets.

This should not be implemented in MVP because it requires a reliable daily grouping mechanism and summary workflow.

### AgentContextSnapshot

`AgentContextSnapshot` may become a denormalized read model for the AI agent.

It can store a compact prebuilt context for a user profile:

- active tracking targets;
- active questions;
- active medicines and reminders;
- communication preferences;
- recent important observations;
- safety rules or agent behavior notes.

In MVP, the system can use normalized data directly. Snapshotting is useful only when context assembly becomes expensive or repetitive.

### Target activity history

In MVP, a tracking target has a simple `is_active` flag.

In V2, this may become a history table that records when a target was active or inactive.

This is important for accurate DayCards and historical summaries.

Example:

```text
digestion target active from 2026-05-01 to 2026-05-20
digestion target inactive from 2026-05-21 to 2026-05-30
digestion target active again from 2026-05-31
```

Without this history, it is difficult to know which targets were active on a past day.

### Advanced pause/resume logic

In MVP, pause/resume can remain simple.

In V2, pausing a tracking target, question, medicine, or reminder may require more careful lifecycle logic:

- who paused it;
- why it was paused;
- from what date;
- until what date;
- whether child objects should be paused automatically;
- whether they should be resumed automatically.

This is intentionally postponed.

## 7. MVP Boundary

The MVP should support only the following core actions:

1. Create and manage a user profile.
2. Create and manage tracking targets.
3. Create questions for tracking targets.
4. Create medicines for tracking targets.
5. Create reminders for medicines.
6. Create shared cron schedules.
7. Generate feedback items from questions and reminders.
8. Let the user answer feedback items.
9. Record important observations.
10. Retrieve feedback and observations for agent context.

This is enough to build a useful Telegram/MCP assistant without overengineering the domain.

## 8. Naming Decisions

The domain uses explicit names:

- `TrackingTarget` instead of symptom or disease;
- `Observation` instead of event;
- `FeedbackItem` instead of day question queue item;
- `ScheduleCron` instead of generic schedule;
- `Medicine` as a broad user-facing term for medicines, supplements, creams, and procedures.

The goal is to keep the language simple and close to the product behavior.

## 9. Current Domain Summary

The MVP domain is centered on configuration and feedback collection.

```text
TrackingTarget defines what to observe.
Question defines what to ask.
Medicine defines what the user takes or applies.
Reminder defines what to remind.
ScheduleCron defines when to trigger questions and reminders.
FeedbackItem stores concrete questions and answers.
Observation stores important notable facts.
```

This model is intentionally smaller than the future V2 design. It is enough for the first working product and leaves room for daily summaries, snapshots, and historical analytics later.
