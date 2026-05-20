# Dialog 4 — Fixed Pending Feedback Workflow with Read-Only Tools

## Context

Dialog 4 repeats the failed pending-feedback scenario from Dialog 3 after a design fix.

In Dialog 3, the backend had already generated scheduled check-in messages, but the agent could not read pending feedback through an MCP resource. The agent explicitly said that it did not have a callable tool for:

```text
health-agent://pending-feedback/{user_profile_id}
```

After that, we added a new `tools_extra.py` module. It duplicates important read-only MCP resources as explicit MCP tools. The most important new tool for this scenario is:

```text
list_pending_feedback
```

This change made backend state visible to the Telegram agent through the same tool-calling interface that was already working for state-changing actions.

---

## Goal

The goal of this dialog was to verify that the agent can now complete the scheduled feedback loop:

```text
cron creates pending feedback
  -> Telegram sends reminders/questions
  -> user asks what questions are pending
  -> agent reads pending feedback through a tool
  -> user answers in natural language
  -> agent matches answers to pending feedback items
  -> backend saves the answers
```

This is an important workflow because it demonstrates that the project is not only able to create schedules and reminders, but can also process the answers produced by scheduled check-ins.

---

## Initial Context Measurement

Before the fixed dialog, the session had been cleared and the context was measured again.

The context usage was approximately:

```text
Messages: 0
Used: ~9295 / 16384 tokens (56%)
Compression progress: 64%
Remaining: ~5041 tokens
```

After adding extra read-only tools, the baseline context became larger than before. Earlier versions of the workspace were around 7000–7600 tokens after cleanup; after adding the extra tools, the baseline was closer to 9000 tokens.

This is an expected trade-off:

```text
More tools -> better agent capability -> larger baseline context
```

The important result is that the workflow became operational.

---

## Step 1 — User Asks for Pending Questions

### User message

```text
Do you have any questions for me today?

If there are pending check-in questions or reminders, please show them to me one by one or as a short list, whichever is easier.
```

### Agent response

```text
Here are the pending check-in questions for today:

| ID | Created | Question |
|---|---|---|
| 35a10157-7f94-4523-84d7-385d6d56bce7 | 11:00 AM | What was your bowel movement like this morning? |
| 5f87810d-b109-4258-b368-750bf591b58a | 11:00 AM | Did you take your stomach medication? |
| 1607a33a-de6e-4918-afca-d5af24744ba0 | 11:00 AM | How are your legs this morning? |
| 2d8d652d-b2f8-4bb0-89c8-c98c58233712 | 11:00 AM | Did you apply the ointment to your legs? |

Feel free to answer them one by one, or let me know if you’d like to skip any.
```

### What happened internally

Unlike Dialog 3, the agent successfully found pending feedback. This confirms that exposing pending feedback as an explicit read-only tool fixed the discovery problem.

The response was a little technical because it included feedback item IDs. However, this is acceptable for a debug/demo dialog: we intentionally wanted to verify that the backend state was being read correctly.

For a production UX, these IDs should probably be hidden by default.

---

## Step 2 — User Answers Multiple Pending Questions Naturally

### User message

```text
I took the stomach medication. My bowel movement this morning was normal, maybe a little soft, but nothing unusual.

I also applied the pain relief ointment to my legs. My legs feel better than yesterday, but I still have mild pain in my left foot.

Please match these answers to my pending questions and save them.
```

### Agent response

```text
All of your pending check-in questions for today have been recorded:

- Bowel movement: normal, slightly soft.
- Stomach medication: taken.
- Leg pain: improved, mild pain in left foot remains.
- Ointment: applied to legs.

Let me know if you’d like to set up any new reminders or tracking targets!
```

### What happened internally

The agent matched one natural-language response to four pending feedback items:

1. Bowel movement question.
2. Stomach medication question.
3. Morning leg pain question.
4. Ointment application question.

The response was concise and user-friendly. It preserved the Health Keeper persona: calm, practical, and focused on tracking rather than diagnosis.

The agent also avoided over-medicalizing the answer. It did not give medical advice or attempt to interpret the symptoms diagnostically.

---

## Technical Result

Dialog 4 confirms that the revised architecture works:

```text
Telegram
  -> PicoClaw
  -> cloud LLM
  -> read-only MCP tool: list_pending_feedback
  -> answer feedback tools
  -> backend use cases
  -> SQLite persistence
  -> Telegram confirmation
```

The key difference from Dialog 3 is that the agent no longer needed to read an MCP resource directly. It used a tool instead.

---

## Why Dialog 3 Failed and Dialog 4 Worked

### Dialog 3

The agent was expected to read:

```text
health-agent://pending-feedback/{user_profile_id}
```

But the Telegram runtime did not expose MCP resources as reliable callable operations for the model. The agent said that it did not have a tool for reading that resource.

### Dialog 4

We added read-only tools that mirror the important resources. The agent could now call `list_pending_feedback` through the normal tool-calling path.

This is the practical conclusion:

```text
For PicoClaw Telegram runtime, important read operations should be available as tools, not only as resources.
```

Resources can still remain useful for MCP Inspector and documentation, but critical agent workflows should use tools.

---

## Impact on Schedule Reuse

This change also explains an earlier limitation from Dialog 2. In the stomach pain setup dialog, the agent created a new 11:00 cron instead of reusing the existing one.

Most likely, the model did not have a reliable way to inspect existing schedules through resources. After adding read-only tools such as:

```text
list_user_schedule_crons
list_user_tracking_targets
list_tracking_target_questions
list_tracking_target_medicines
```

the agent should be better able to inspect existing backend state before creating new objects.

A future improvement would be to move this logic fully into backend use cases:

```text
get_or_create_schedule_cron
get_or_create_tracking_target
get_or_create_medicine
get_or_create_reminder
```

This would make reuse deterministic and would not rely on the model reading a list correctly.

---

## Context Budget Trade-Off

After adding extra read-only tools, context usage increased. This is expected because each tool adds schema and description to the model context.

In this demo, the context after the final answer was approximately:

```text
Messages: 18
Used: ~12135 / 16384 tokens (74%)
Compression progress: 84%
Remaining: ~2201 tokens
```

This shows a real engineering trade-off:

```text
More tools improve reliability, but increase baseline context.
```

For the course project, this is acceptable because the goal is to demonstrate a rich agent with tools, skills, backend state, and scheduled automation.

For production, the better design would be:

- fewer but more powerful read tools;
- compact `AgentContextSnapshot`;
- `get_or_create_*` backend operations;
- smaller runtime workspace;
- multiple specialized agents instead of one large agent.

---

## Evidence

This dialog is supported by:

- Telegram screenshots showing pending questions and saved answers;
- MCP logs showing read-only tool calls and answer-feedback calls;
- API logs showing scheduled execution and pending feedback creation;
- SQLite state showing persisted feedback items.

Raw logs should be sanitized before being included in the public report because they may contain Telegram IDs and health-related text.

---

## Conclusion

Dialog 4 confirms that the failed workflow from Dialog 3 was fixed.

The main result:

```text
Before:
  pending feedback existed, but the agent could not read it through resources.

After:
  pending feedback is exposed as a read-only tool, and the agent successfully lists and answers pending questions.
```

This is a strong end-to-end result. It demonstrates scheduled backend automation, Telegram delivery, pending feedback persistence, agent-side matching of natural-language answers, and successful state updates through MCP tools.

The final workflow is operational, although the project now has a larger context footprint due to the additional tools.
