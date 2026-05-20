# V2 Ideas

This document collects ideas intentionally left outside the MVP.

The MVP focuses on a reliable agent loop:

```text
Telegram / PicoClaw
  -> cloud or local LLM
  -> MCP tools/resources/prompts
  -> application use cases
  -> SQLite
  -> FastAPI/APScheduler
  -> Telegram notifications
```

The current implementation already supports the core product loop:

```text
create or recover user profile
  -> create tracking targets
  -> schedule questions and reminders
  -> create pending feedback
  -> answer or skip feedback
  -> record observations
  -> inspect state through resources
```

V2 should not simply add more features. The main V2 direction is to make the system more reliable, easier for the agent to use, and cheaper in LLM context.

---

## 1. Identity and Session State

### Current status

The MVP already works with Telegram-based identity:

```text
telegram_user_id  -> external Telegram user integer
telegram_chat_id  -> external Telegram chat integer
user_profile_id   -> internal database UUID
```

For a private Telegram chat, `telegram_user_id == telegram_chat_id`.

The agent can recover or create a `UserProfile`, and the generated `user_profile_id` can remain visible in chat history. This was enough for the demo flow.

### V2 improvement

Add a more explicit session-state bridge:

```text
PicoClaw session / channel metadata
  -> telegram_user_id
  -> user_profile_id
  -> agent session memory
```

The goal is to avoid asking the user for IDs and avoid repeatedly resolving the same profile.

Possible implementation:

- extract Telegram identity from stable PicoClaw/OpenClaw metadata;
- store the resolved `user_profile_id` in session-scoped memory when possible;
- expose a small MCP resource such as `health-agent://current-session`;
- make bootstrap idempotent and silent when the profile is already known.

This is a refinement, not a blocker: the MVP already works, but V2 should make identity recovery more automatic and less visible to the user.

---

## 2. Agent Context Snapshot

`AgentContextSnapshot` can become a denormalized read model optimized for the LLM.

The MVP currently assembles agent context from normalized resources. This is clean, but it may require several calls:

```text
profile
tracking targets
schedule crons
questions
medicines
reminders
pending feedback
recent observations
```

V2 can provide one compact resource:

```text
health-agent://agent-context/{user_profile_id}
```

It may contain:

- profile basics;
- active tracking targets;
- active questions;
- active medicines/creams/procedures;
- active reminders;
- active schedules;
- pending feedback summary;
- recent observations;
- safety notes;
- known timezone/language.

This would reduce tool/resource round-trips and help the model avoid creating duplicate schedules or duplicate targets.

---

## 3. Resource-First / Get-Or-Create Operations

### Current limitation

During the demo, the agent sometimes created a new 11:00 schedule instead of reusing an existing one. The system still worked, but it showed that relying only on resources and prompt instructions is not always enough.

### V2 improvement

Add dedicated idempotent use cases and MCP tools:

```text
get_or_create_tracking_target
get_or_create_schedule_cron
get_or_create_medicine
get_or_create_question
get_or_create_reminder
```

This would move reuse logic from the LLM into deterministic backend code.

Example:

```text
get_or_create_schedule_cron(
  user_profile_id=...,
  cron="0 11 * * *",
  title_hint="Morning check-in"
)
```

The backend should return the existing schedule if one already matches. This is safer than asking the model to inspect resources and choose correctly.

---

## 4. DayCard

A `DayCard` can represent one local user day.

The system stores timestamps in UTC, but users think in local days.

A future `DayCard` can store:

- user profile ID;
- local date;
- timezone snapshot;
- UTC start;
- UTC end;
- optional daily summary;
- status of pending/answered feedback for that day.

This would make it easier to group feedback and observations by user-local day.

---

## 5. DayTargetSummary

A `DayTargetSummary` can summarize one tracking target inside one local day.

Examples:

```text
Day 2026-05-17, digestion:
  mild discomfort in the evening, no morning episode

Day 2026-05-17, leg pain:
  pain increased after walking, cream applied once
```

This would allow separate summaries for:

- digestion;
- leg pain;
- joint pain;
- headache;
- sleep;
- general wellbeing.

It is outside MVP because it requires reliable daily grouping, timezone semantics, and summarization policy.

---

## 6. Local-Day Feedback Windows

The MVP can read feedback and observations by explicit time windows.

V2 should provide user-local day resources:

```text
health-agent://day/{user_profile_id}/{local_date}
health-agent://day-target/{user_profile_id}/{local_date}/{tracking_target_id}
```

This would hide UTC conversion from the agent.

It would also make prompts shorter because the model could ask for "today" or "yesterday" through a stable backend resource rather than calculating dates itself.

---

## 7. User-Local Schedule Semantics

MVP stores cron expressions directly and currently treats cron timing as a backend scheduling detail.

V2 may add user-local schedule abstractions:

```text
morning
evening
after breakfast
before lunch
after dinner
every 2 days
weekdays only
```

The backend can compile these concepts into cron expressions using the user's timezone.

This would improve UX because users usually say:

```text
ask me every morning
remind me before lunch
```

not:

```text
0 11 * * *
```

---

## 8. Notification Bundling

The MVP sends messages when schedules fire.

V2 should improve notification strategy:

- merge several questions/reminders scheduled at the same time;
- avoid Telegram spam;
- group pending feedback by target;
- mention only the most relevant unanswered items;
- support quiet hours;
- optionally send a single "morning check-in" card.

This is especially useful when multiple questions and reminders share one schedule.

---

## 9. Scheduler Worker Process

MVP hosts APScheduler inside the FastAPI process.

V2 may move scheduler runtime into a dedicated worker process:

```text
health-mcp
health-api
health-scheduler-worker
```

This would make the scheduler more production-like and easier to supervise.

The current FastAPI/APScheduler solution is sufficient for the course demo, but a worker process would be cleaner for deployment.

---

## 10. Scheduler Reliability and Recovery

V2 should improve scheduler recovery:

- reload jobs from active `ScheduleCron` rows on startup;
- detect missing APScheduler jobs;
- avoid duplicate job registration;
- expose scheduler status resources;
- store last run time and next run time;
- record execution errors in a safe log table.

This would make scheduled reminders easier to debug.

---

## 11. Target Activity History

In MVP, `TrackingTarget` has a simple `is_active` flag.

V2 can introduce lifecycle history:

```text
tracking_target_id
status
active_from
active_until
reason
```

This matters for historical summaries.

If a target was inactive on a past day, day summaries should know that.

---

## 12. Advanced Pause/Resume Logic

MVP can keep pause/resume simple.

V2 can model lifecycle more carefully:

- who paused an item;
- why it was paused;
- from what date;
- until what date;
- whether child questions/reminders should pause automatically;
- whether resume should restore previous child states.

This is especially important for tracking targets, because they aggregate questions, medicines, and reminders.

---

## 13. Admin / Debug API

MVP has only scheduler-control endpoints.

V2 may add safe internal endpoints for debugging:

- list users;
- list profiles;
- list tracking targets;
- list schedule crons;
- list pending feedback;
- list recent observations;
- inspect APScheduler jobs;
- inspect MCP tool-call outcomes.

These endpoints should be internal-only and should not become the agent's normal user interface.

---

## 14. Better Agent-Facing Resources

The current MCP design already uses resources for read-only state.

V2 can improve the shape of these resources:

```text
health-agent://profile/{user_profile_id}
health-agent://tracking-setup/{user_profile_id}
health-agent://pending-feedback/{user_profile_id}
health-agent://today/{user_profile_id}
health-agent://recent/{user_profile_id}/{days}
```

The main goal is to give the agent compact, task-oriented context instead of requiring it to stitch together many small resources.

---

## 15. Skills and Context Budget

The project tested PicoClaw skills. Skills work, but they also increase baseline context.

V2 should separate two workspaces:

```text
rich workspace      -> detailed skills and documentation for evaluation/reporting
runtime workspace   -> compressed instructions for real inference
```

A production version could split the system into several specialized agents:

```text
Supervisor / Router Agent
  -> Profile Agent
  -> Tracking Setup Agent
  -> Reminder Agent
  -> Feedback Agent
  -> Analysis Agent
```

Each specialized agent would have a smaller context and a smaller skill set.

This would reduce token usage and make behavior more predictable.

---

## 16. Prompt and Skill Consolidation

The project uses both MCP prompts and PicoClaw skills.

V2 should keep the boundary clear:

```text
Skills      -> operational workflows
MCP prompts -> reusable analytical/report templates
Tools       -> state-changing commands
Resources   -> read-only state
```

Some workflows can be represented either as skills or prompts. V2 should avoid duplicating the same long workflow in both places.

---

## 17. Richer Analysis Workflow

The current `analyze_user_state` prompt is intentionally simple.

V2 can add richer analysis workflows:

- compare recent days;
- detect missing data;
- suggest better questions;
- identify possible correlations;
- prepare doctor-facing summaries;
- separate facts from hypotheses;
- explain uncertainty.

The agent still must not diagnose, prescribe, or change treatment.

---

## 18. Export and Reports

V2 can add exports:

- weekly markdown summary;
- CSV export;
- doctor-facing PDF;
- timeline report;
- supplement reaction report;
- prompt-generated interaction report for course/demo evidence.

This would make the assistant more useful outside Telegram.

---

## 19. Web Search Tool

The project considered adding web search.

It was removed from MVP because it is not core to the current business value.

Future search tools could help the agent look up:

- medication information;
- supplement side effects;
- official medical references;
- general safety information.

This should be implemented carefully and clearly separated from the user's recorded health data.

Possible future ports:

```text
WebSearch
WebPageFetcher
```

The agent should cite sources and avoid replacing professional medical advice.

---

## 20. Source Reading / Web Page Fetching

Search alone only returns snippets.

If web search is added, the agent may also need:

```text
fetch_web_page(url)
```

This introduces complexity:

- HTML parsing;
- redirects;
- PDFs;
- page length limits;
- unreliable pages;
- source quality.

This is why it is left outside MVP.

---

## 21. Data Privacy Improvements

Health-related data is sensitive.

V2 can add:

- encrypted database;
- redaction in logs;
- data export/delete tools;
- stronger multi-user isolation;
- audit log for tool calls;
- explicit retention policy;
- sanitized report generation.

Raw logs and database snapshots should not be attached to public reports without redaction.

---

## 22. Multi-User and Group Chat Support

MVP is optimized for one private Telegram chat.

V2 can improve:

- multiple Telegram users with one bot;
- group chat mentions;
- per-user isolation in groups;
- chat-specific context;
- privacy constraints.

Group chats are intentionally not part of MVP because Telegram identity and privacy semantics become more complex.

---

## 23. Testing Strategy

MVP is focused on implementation and demo.

V2 can add tests:

- domain tests;
- repository tests;
- use case tests;
- scheduler execution tests;
- MCP tool smoke tests;
- MCP resource smoke tests;
- Telegram sender tests with fake transport;
- SQLite integration tests;
- agent workflow regression tests using fixed prompts.

The most important test category for V2 is idempotency:

```text
same user asks twice
same schedule requested twice
same target requested twice
same reminder requested twice
```

The backend should avoid duplicates where reuse is expected.

---

## 24. V2 Summary

The MVP proves that the Health Keeper loop works:

```text
configure tracking
  -> schedule questions/reminders
  -> collect feedback
  -> record observations
  -> provide context for agent analysis
```

V2 should focus on reliability and agent ergonomics:

- better session identity;
- compact agent context snapshots;
- get-or-create backend operations;
- local-day abstractions;
- better schedule reuse;
- notification bundling;
- safer logs and reports;
- clearer split between skills, prompts, tools, and resources.

The key lesson is that prompt instructions alone are not enough for all workflows. Reuse, identity, and idempotency should move into backend use cases wherever possible.
