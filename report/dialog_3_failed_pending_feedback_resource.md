# Dialog 3 — Failed Pending Feedback Discovery and Design Fix

## Context

This dialog is a negative test case. It was performed after scheduled cron messages had already been delivered to Telegram.

The backend scheduler worked correctly: two scheduled check-ins were sent to the user:

```text
Reminders:
- Please remember to take your stomach medication.

Questions:
- What was your bowel movement like this morning?
- Did you take your stomach medication?

Reminders:
- Please apply the pain relief ointment to your legs.

Questions:
- How are your legs this morning?
- Did you apply the ointment to your legs?
```

The expected next step was for the agent to read pending feedback from the backend, show the user the open questions, and then match the user's answers to the correct pending feedback items.

This dialog tested whether the agent could discover pending feedback through MCP resources after the Telegram session had been cleared.

---

## Goal

The goal was to verify this workflow:

```text
User asks whether there are pending questions
  -> agent recovers user profile
  -> agent reads pending feedback from backend
  -> agent shows pending questions
  -> user answers
  -> agent saves answers
```

This is an important workflow because it tests the full scheduled feedback loop:

```text
ScheduleCron
  -> backend cron execution
  -> pending feedback creation
  -> Telegram notification
  -> agent feedback collection
```

---

## Step 1 — User Asks for Pending Questions

### User message

```text
Do you have any questions for me today?

If there are pending check-in questions or reminders, please show them to me one by one or as a short list, whichever is easier.
```

### Agent response

```text
I don’t see any pending check-in questions for today. If you’d like to add a new question, set up a reminder, or share any observations, just let me know!
```

### What went wrong

The answer was incorrect. The Telegram chat already showed scheduled check-in questions from the backend. Therefore, pending feedback existed conceptually, and the agent should have checked backend state before answering.

The likely reason is that the agent did not read the MCP resource:

```text
health-agent://pending-feedback/{user_profile_id}
```

Instead, it answered from its current conversation context.

---

## Step 2 — User Explicitly Asks to Read Backend Pending Feedback

### User message

```text
I think there are pending check-in questions from today’s scheduled reminders.

Please read my pending feedback from the backend before answering. Use the pending feedback resource for my current Health Keeper profile.

After reading it, show me the pending questions as a short numbered list.
```

### Agent response

```text
I’d like to show you exactly what’s waiting for your responses, but I don’t have a tool that can read the pending-feedback resource directly.
Could you share the list of today’s pending questions (or the feedback-item IDs) that you see in the Health Keeper app? Once I have that, I can match your answers to the right slots and save them.
```

### What went wrong

The agent explicitly stated that it did not have a callable tool for reading pending feedback. This confirmed that the Telegram/PicoClaw runtime was not exposing MCP resources to the model as callable operations in the same reliable way as MCP tools.

---

## Step 3 — User Explicitly Names the MCP Resource

### User message

```text
Please use this MCP resource:
health-agent://pending-feedback/{user_profile_id}
```

### Agent response

```text
I’m sorry, but I don’t have a built-in tool that can pull the health-agent://pending-feedback/<user_profile_id> URL directly.

If you could paste the list of today’s pending questions (or the feedback-item IDs) that appear in the Health Keeper app, I’ll match them to the right slots and give you a numbered list right away.
```

### What went wrong

Even after the user explicitly named the resource URI, the agent still could not read it. This means that, at least in our current PicoClaw + Telegram runtime, MCP resources are not a reliable operational interface for the model.

This does not mean that resources are useless. They may still be visible in MCP Inspector and remain useful for debugging or documentation. However, they were not sufficient for the Telegram-agent workflow.

---

## Technical Finding

The main finding from this failed dialog is:

```text
MCP resources are not reliably callable by the PicoClaw Telegram agent.
MCP tools are reliably callable.
```

This explains why previous state-changing operations worked:

```text
create_user_profile
create_tracking_target
create_schedule_cron
create_question
create_medicine
create_reminder
record_observation
```

They were all MCP tools.

But read-only state discovery through resources did not work reliably:

```text
health-agent://pending-feedback/{user_profile_id}
```

The agent did not call a resource read operation and instead asked the user to paste the pending questions manually.

---

## Design Fix

To fix this, we decided to duplicate important MCP resources as explicit read-only MCP tools.

The new file is:

```text
src/health_agent/adapters/inbound/mcp/tools_extra.py
```

It registers read-only tools that mirror the resource layer.

Examples:

```text
read_user_profile_context
list_user_tracking_targets
list_user_schedule_crons
list_tracking_target_questions
list_tracking_target_medicines
list_medicine_reminders
list_pending_feedback
list_feedback_window
list_observations_window
```

These tools do not mutate backend state. They only expose backend state through the normal tool-calling interface, which the Telegram agent can actually use.

---

## Why This Is a Reasonable Fix

In theory, MCP resources are the correct primitive for read-only state. In practice, for this runtime, tools are the more reliable interface.

The revised architecture is therefore:

```text
MCP tools:
  - state-changing commands
  - important read-only operations required by the agent

MCP resources:
  - inspector/debug/documentation interface
  - optional read-only state interface

MCP prompts:
  - reusable analytical/reporting templates
```

This is a pragmatic compromise. It keeps the resource layer, but does not rely on it for critical agent behavior.

---

## Engineering Lesson

This failed dialog is useful because it exposed a real integration boundary.

The backend worked:

- cron messages were sent;
- scheduled questions existed;
- Telegram notification delivery worked.

The LLM/MCP integration partially failed:

- the agent could not read pending feedback through an MCP resource;
- it did not know how to call `health-agent://pending-feedback/{user_profile_id}`;
- it asked the user to manually paste backend state.

The solution is to move frequently used read paths into tools. This is especially important for workflows where the agent must make a decision based on backend state.

---

## Report Note

This dialog should be included in the final report as an example of debugging and iteration.

It shows that the project was not only a scripted success path. We discovered a limitation, analyzed it, and changed the MCP design:

```text
Before:
  pending feedback was available only as an MCP resource

After:
  pending feedback is also available through list_pending_feedback tool
```

This also motivates one of the V2 ideas:

```text
AgentContextSnapshot
```

A compact `get_agent_context` or `list_pending_feedback` tool is often more reliable than asking a general-purpose agent to discover several resources by itself.

---

## Conclusion

Dialog 3 was intentionally unsuccessful. It demonstrated that the scheduled backend loop works, but the agent could not access pending feedback through MCP resources in the Telegram runtime.

The fix is to expose important read-only resources as explicit MCP tools. After this change, the same scenario can be tested again as Dialog 4, where the agent should list pending feedback and match user answers correctly.
