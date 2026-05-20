# AI-ассистент: Health Keeper

## Модель

В начале проекта мы попробовали запустить агента локально через Ollama. Это был самый привлекательный вариант с архитектурной точки зрения: health-related данные остаются на машине пользователя, агент не зависит от внешнего API, а локальная модель лучше соответствует идее приватного персонального ассистента.

Первая рабочая конфигурация использовала локальную Llama 3.1/3.x 8B на MacBook с Apple M1 и 16 GB RAM. Технически такой запуск возможен, но для нашего агентного сценария модель оказалась недостаточно стабильной. Во-первых, локальный inference сильно нагружал ноутбук: температура поднималась примерно до 90°C, а ответы генерировались медленно. Во-вторых, качество tool-calling было нестабильным: модель путала Telegram user ID, Telegram chat ID и внутренний `user_profile_id`.

Для нашего проекта это критично, потому что Telegram ID — это внешний идентификатор пользователя, а `user_profile_id` — внутренний UUID из базы данных. Если модель передаёт Telegram ID туда, где backend ждёт UUID, use case падает. В ранних MCP-логах (`logs/mcp_old.log`) это действительно происходило: модель могла вызвать tool с placeholder-значением или внешним ID вместо настоящего `user_profile_id`.

После этого мы протестировали несколько cloud inference providers:

- **Groq** — быстрый provider, но бесплатные лимиты по tokens per minute оказались слишком маленькими для нашего workspace. Один запрос агента с `AGENT.md`, `USER.md`, `SOUL.md`, `TOOLS.md`, skills и tool schemas уже занимал значительную часть лимита.
- **Gemini** — выглядит сильным вариантом по token budget, но бесплатный tier оказался неудобным для регулярных экспериментов из-за ограничения по requests per day.
- **Cerebras** — корректно работал с tool-calling, но доступный набор моделей был менее удобен для нашего MVP: либо маленькая Llama с ограниченным контекстом, либо слишком мощная `gpt-oss-120b`, которая избыточна для нашего сервиса.
- **Ollama Cloud** — оказался самым удобным вариантом для демонстрации. Мы проверили `gpt-oss:120b-cloud`, а затем перешли на более лёгкую `gpt-oss:20b-cloud`.

Финальный demo запускался на **Ollama Cloud `gpt-oss:20b-cloud`**. Эта модель стала хорошим компромиссом: она существенно сильнее локальной 8B-модели, но не такая избыточная, как 120B-модель. Она корректно возвращала structured `tool_calls` через OpenAI-compatible endpoint, не путала основные ID в демонстрационных сценариях и позволила провести end-to-end тесты через Telegram, PicoClaw, MCP и backend.

### Почему нет отдельного Modelfile

В задании упоминается model file. Для локального Ollama-сценария это действительно полезно: можно создать wrapper над базовой моделью, добавить system prompt, параметры и локальные инструкции.

В нашем финальном варианте отдельный Ollama `Modelfile` не используется осознанно. Поведение агента задаётся не через wrapper модели, а через **PicoClaw workspace**:

```text
AGENT.md
USER.md
SOUL.md
TOOLS.md
skills/
```

Если бы мы дополнительно создали `Modelfile`, у нас появились бы две точки конфигурации поведения: одна в Ollama, другая в PicoClaw. Это создало бы риск рассинхронизации инструкций. Поэтому в финальной архитектуре модель остаётся inference backend-ом, а agent behavior задаётся workspace-файлами и MCP-интерфейсом.

### Язык взаимодействия

Диалоги с агентом в demo проводились на английском языке. Это связано с тем, что workspace-файлы, tool descriptions, skills и prompts написаны на английском. Для Qwen/GPT-OSS-подобных моделей такое взаимодействие более естественно и снижает риск ошибок в tool selection.

GigaChat не использовался не из-за технической невозможности, а потому что выбранный стек лучше соответствовал англоязычным agent-инструкциям и Ollama/GPT-OSS экспериментам.

Итоговый выбор модели был инженерным компромиссом между приватностью, стоимостью, размером контекста, качеством tool-calling и доступными вычислительными ресурсами. В production-сценарии для health-assistant лучше использовать локальную или self-hosted модель достаточного размера. Для учебного MVP мы выбрали Ollama Cloud `gpt-oss:20b-cloud`, потому что она позволила стабильно показать реальные agent workflows.

---

## Персона

Health Keeper — это спокойный персональный health-observation ассистент. Он не является врачом, не ставит диагнозы, не назначает лечение и не меняет дозировки препаратов.

Его задача — помогать пользователю вести наблюдения:

- создавать профили;
- заводить tracking targets;
- настраивать вопросы;
- создавать напоминания;
- собирать pending feedback;
- записывать важные observations;
- помогать анализировать уже сохранённое состояние.

Персона у проекта не развлекательная, а практическая. Бот иногда возвращает технические ID, потому что текущая демонстрация проверяет persistence, MCP tools и backend state. В нормальном пользовательском режиме ID можно скрывать или показывать только при debug-запросах.

Главный тон ассистента:

- спокойный;
- осторожный;
- не медицински категоричный;
- ориентированный на факты;
- не пытающийся заменить врача.

---

## Скиллы

В проекте реализованы 8 skills. Они находятся в `picoclaw_workspace/skills/` и описывают процедурные сценарии поведения агента.

### 1. `bootstrap-user-profile`

Скилл отвечает за первичную идентификацию пользователя.

Он помогает агенту:

- понять разницу между Telegram ID и `user_profile_id`;
- восстановить профиль через Telegram ID;
- создать профиль, если он отсутствует;
- сохранить или вывести `user_profile_id`, чтобы дальше работать с backend-сущностями.

Это один из самых важных skills, потому что ранние локальные модели часто путали внешние Telegram IDs и внутренние UUID.

### 2. `setup-tracking-target`

Скилл создаёт или переиспользует tracking target.

Примеры:

- leg pain;
- stomach pain;
- digestion;
- sleep;
- general wellbeing.

Tracking target — это долгоживущая тема наблюдения, к которой затем привязываются вопросы, лекарства, напоминания и observations.

### 3. `setup-recurring-question`

Скилл помогает создать регулярный вопрос.

Например:

```text
How are your legs this morning?
What was your bowel movement like this morning?
```

Он должен связать вопрос с tracking target и schedule cron.

### 4. `setup-medicine-reminder`

Скилл создаёт сущность medicine/supplement/cream/procedure и привязывает к ней reminder.

В MVP слово `medicine` используется широко. Это может быть:

- medicine;
- supplement;
- cream;
- ointment;
- procedure;
- routine.

Например, в demo мы создали reminder для pain relief ointment и отдельный reminder для stomach medication.

### 5. `review-pending-feedback`

Скилл читает pending feedback items и показывает пользователю, какие вопросы ещё нужно закрыть.

Это read-oriented workflow: агент не должен создавать новые observations или questions, если пользователь просто спрашивает, что осталось ответить.

### 6. `answer-or-skip-feedback`

Скилл связывает пользовательский ответ с pending feedback item.

Например, если scheduled reminder спросил:

```text
Did you apply the ointment to your legs?
```

пользователь может ответить:

```text
Yes, I applied it. My left foot still hurts a little.
```

Агент должен найти подходящий pending item и вызвать `answer_feedback`. Если пользователь говорит, что не помнит или хочет пропустить вопрос, используется `skip_feedback`.

### 7. `record-important-observation`

Скилл записывает важное наблюдение.

Observation отличается от routine feedback. Feedback — это ответ на регулярный вопрос. Observation — это заметный факт, который пользователь специально хочет сохранить.

Пример из demo:

```text
When I woke up this morning, I had mild pain in my left foot.
```

### 8. `analyze-known-state`

Скилл описывает read-only анализ уже сохранённого состояния.

Он должен использовать MCP resources (или read-only tools), а не создавать новые записи. Его задача — собрать профиль, tracking targets, pending feedback, feedback windows и observations, а затем аккуратно описать состояние пользователя без диагнозов.

---

## Критерии оценивания

Ниже — самооценка проекта по критериям задания.

| Критерий | Как закрыт в проекте |
|---|---|
| Бот работает с идеей/пользователем | Бот реально работает через Telegram. Мы проверили цепочку `Telegram -> PicoClaw -> LLM -> MCP -> backend -> SQLite`. |
| Персона держится | Персона Health Keeper выдержана: бот не врач, не ставит диагнозы, помогает вести наблюдения и напоминания. |
| Скилл реализован | Реализовано 8 skills, которые покрывают bootstrap, tracking setup, recurring questions, reminders, pending feedback, observations и analysis. |
| Tools используются | MCP tools реально вызывают application use cases и меняют состояние в SQLite. После отладки добавлены также read-only tools для чтения backend state. Это не имитация JSON-ответов в чате. |
| Resources используются | Read-only состояние вынесено в MCP resources: profile, tracking targets, schedule crons, questions, medicines, reminders, pending feedback, feedback/observation windows. После Dialog 3 ключевые resources также продублированы как read-only tools, потому что Telegram runtime надёжнее работает с tools. |
| Prompts используются | MCP prompts оставлены для аналитических и отчётных workflows, например `analyze_user_state` и `summarize_interaction_for_report`. |
| Конфиги полные | Есть PicoClaw workspace, example config/security files, MCP server, backend settings и отдельные entrypoints. Секреты не включаются в репозиторий. |
| Отчёт ясный | Проект содержит README, docs, report files и отдельные markdown-документы по архитектуре, MCP design, adapters layer и V2 ideas. |
| Автоматизация по cron | Реализован отдельный FastAPI/APScheduler backend. Агент создаёт schedule configuration, а backend исполняет cron и отправляет Telegram-сообщения. |
| Состояние сохраняется | Состояние хранится в SQLite: user profiles, targets, schedules, questions, medicines, reminders, feedback items, observations. |
| Груповой чат не поддерживается из-за архитектурных соображений | Как показали примеры бот может сам создавать профили пользователей для хренения данных в бд, подтягивая tg user id из сессии. Этот id служит авторизацией в систему и позволяет отправлять напоминания по cron job (id пользователя совпадает с id чатом). Использование бота в группе сломает эту замечательную механику - потребует регистрировать user profile на целую группу, что немного странно. Да и обсуждать, что болит у одного человека в группе, странно, неэтично, неправильно. Поэтому бот в группу не добавляется, этот сценарий не имеет смысла. |
| Несколько skills в связке | В demo один пользовательский сценарий проходит через несколько skills: profile bootstrap, target setup, question setup, reminder setup, observation recording. |
| Backend сложнее минимального примера | Проект не ограничивается prompt-only агентом. Есть полноценный backend, use cases, repositories, UnitOfWork, scheduler runtime и Telegram sender. |

### Почему scheduler вынесен в backend

В задании можно было бы сделать простую cron-like автоматизацию внутри агента. Мы выбрали другой вариант: агент не должен быть runtime-процессом, который сам «просыпается» по расписанию.

В нашей архитектуре:

```text
MCP tool creates schedule configuration
FastAPI/APScheduler registers and executes cron
ScheduleExecutionService creates pending feedback
Telegram sender sends reminders/questions
SQLite stores state
```

Это ближе к production-подходу: расписание не теряется при очистке чата и не зависит от текущего LLM context.

---

## Что было непросто

### 1. Локальная модель оказалась слабой

Локальный inference на MacBook M1 16 GB RAM оказался тяжёлым. Модель работала медленно, грела ноутбук и хуже следовала tool-calling логике.

### 2. Модели путали ID

Самая важная техническая проблема — различие между:

```text
telegram_user_id
telegram_chat_id
user_profile_id
tracking_target_id
schedule_cron_id
```

Слабые модели могли передавать Telegram ID вместо UUID. Поэтому мы отдельно описали identity policy в workspace и skills.

### 3. Tool-calling отличается у разных providers

Не все модели одинаково возвращают tools. Некоторые пишут JSON в обычный текст, некоторые возвращают structured `tool_calls`, некоторые имеют слишком маленькие limits. Для проекта был важен именно structured tool-calling, потому что PicoClaw должен реально вызвать MCP tool, а не просто отправить JSON пользователю.

### 4. Подробные workspace-файлы увеличивают context

Для оценки задания полезно иметь подробные:

```text
AGENT.md
USER.md
SOUL.md
TOOLS.md
skills/
```

Но для реального inference это увеличивает baseline context. Это инженерный конфликт: чем лучше документация агента, тем дороже каждый запрос.

В production-версии мы бы разделили систему на несколько специализированных агентов:

```text
Supervisor / Router Agent
  -> Profile Agent
  -> Tracking Setup Agent
  -> Reminder Agent
  -> Feedback Agent
  -> Analysis Agent
```

У каждого агента был бы меньший context и меньший набор skills.

### 5. Schedule reuse не всегда идеален

Во втором demo агент корректно создал stomach pain target, question, medicine и reminder, но создал новый 11:00 schedule вместо переиспользования существующего. Это не ломает систему, но показывает, что resource-first поведение стоит усилить.

Лучшее V2-решение:

```text
get_or_create_schedule_cron
get_or_create_tracking_target
get_or_create_medicine
```

Тогда reuse будет deterministic backend logic, а не надежда на LLM.

### 6. Задание предполагает простой агент, а проект стал backend-системой

Для устойчивой работы health-assistant мало иметь только prompt и один tool. Нужны:

- database;
- repositories;
- use cases;
- scheduler;
- Telegram sender;
- MCP tools/resources;
- logging;
- identity rules.

Поэтому проект получился больше, чем минимальный архив с несколькими markdown-файлами. Это осознанное решение: мы делали не toy chatbot, а маленький production-like MVP.

---

## Вывод

Проект показал, что Health Keeper работает как реальная агентная система, а не только как текстовая симуляция.

Мы проверили end-to-end цепочку:

```text
Telegram
  -> PicoClaw gateway
  -> cloud LLM
  -> MCP tools/resources/prompts
  -> application use cases
  -> SQLite
  -> FastAPI/APScheduler
  -> Telegram notifications
```

В demo были проверены:

- user profile creation and recovery;
- leg pain tracking target;
- stomach pain tracking target;
- schedule crons;
- recurring questions;
- medicine/cream reminders;
- pending feedback creation;
- feedback answer matching;
- observations;
- daily summary;
- tracking target deactivation without deleting history.

Главная польза такого ассистента — не в медицинских советах, а в регулярном сборе данных. Пользователь часто забывает, когда были симптомы, принимал ли он препарат, была ли реакция после еды или добавки. Health Keeper помогает превращать такие события в structured history.

Буду ли я пользоваться таким ассистентом? В текущем виде — как technical prototype. Для реального личного использования нужно улучшить UX, скрыть лишние IDs, добавить `get_or_create` логику и лучше сгруппировать уведомления. Но core loop уже работает.

Что бы я улучшил в первую очередь:

1. `get_or_create_*` tools для избежания дублей.
2. Agent context snapshot resource.
3. User-local day summaries.
4. Notification bundling.
5. Более компактный runtime workspace.
6. Отдельные specialized agents вместо одного большого агента.

После данных обновлений я разверну на VPS и буду отслеживать свои проблемы с пищеварением и болями в стопах. Это можно сделать на маленьком VPS по причине использования облачного llm inference - еще одна причина ухода от локальной модели на текущем этапе. 

---

## Примеры диалогов

В проекте подготовлены отдельные dialog files на английском языке. Диалоги велись на английском, потому что workspace, tools, prompts и skills также написаны на английском.

### Dialog 1 — Technical End-to-End Demo

Первый диалог был техническим. Пользователь явно передавал IDs, чтобы проверить backend path.

В нём были проверены:

- profile bootstrap;
- tracking target creation;
- schedule cron creation;
- recurring question creation;
- medicine/reminder creation;
- observation recording.

Этот диалог доказывает, что система сохраняет состояние в SQLite и вызывает реальные MCP tools.

Файл:

```text
report/dialog_1_health_keeper_technical_demo.md
```

### Dialog 2 — Natural User-Friendly Demo

Второй диалог был более естественным. Пользователь не передавал internal IDs вручную и просил настроить stomach pain tracking обычным языком.

В нём были проверены:

- profile recovery после очистки сессии;
- natural tracking target creation;
- creation of additional question;
- stomach medication reminder;
- feedback question;
- partial schedule reuse limitation.

Файл:

```text
report/dialog_2_health_keeper_natural_demo.md
```

### Dialog 3 — Failed Pending Feedback Discovery

Третий диалог был намеренно зафиксирован как неудачный сценарий. Cron и Telegram delivery уже сработали: пользователь получил scheduled reminders и questions. Затем пользователь спросил у агента, есть ли сегодня вопросы.

Агент должен был прочитать pending feedback из backend state, но не смог использовать MCP resource:

```text
health-agent://pending-feedback/{user_profile_id}
```

Даже после явной просьбы использовать этот resource агент ответил, что у него нет callable tool для чтения pending feedback. Это показало важное ограничение текущего PicoClaw Telegram runtime: **MCP resources не были надёжным интерфейсом для agent decision-making**.

Вывод из Dialog 3: важные read-only paths нужно дублировать как MCP tools. После этого был добавлен отдельный модуль:

```text
src/health_agent/adapters/inbound/mcp/tools_extra.py
```

Он добавляет read-only tools, которые повторяют ключевые resources:

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

Файл:

```text
report/dialog_3_failed_pending_feedback_resource.md
```

### Dialog 4 — Fixed Pending Feedback Workflow

Четвёртый диалог повторил сценарий Dialog 3 после исправления. После добавления `tools_extra.py` агент смог вызвать `list_pending_feedback`, получить список pending questions и показать их пользователю.

Пользователь ответил одним естественным сообщением сразу на несколько вопросов:

- принял stomach medication;
- bowel movement был нормальный, слегка мягкий;
- применил ointment для ног;
- ноги стали лучше, но mild pain in left foot сохранилась.

Агент сопоставил один свободный текстовый ответ с несколькими pending feedback items и сохранил ответы. Это подтвердило, что scheduled feedback loop работает end-to-end:

```text
APScheduler fires cron
  -> backend creates pending feedback
  -> Telegram sender sends reminders/questions
  -> agent lists pending feedback through tools
  -> user answers naturally
  -> agent saves feedback answers
```

Также в Dialog 4 видно trade-off: после добавления read-only tools baseline context вырос. Это ожидаемо, потому что каждая tool schema попадает в context. Но надёжность workflow стала выше.

Файл:

```text
report/dialog_4_fixed_pending_feedback_tools.md
```

### Dialog 5 — Daily Summary and Target Deactivation

Пятый диалог был финальным user-facing сценарием. После очистки сессии пользователь попросил подвести итог сегодняшним health-tracking данным.

Агент восстановил профиль, прочитал backend state и сделал summary:

- active tracking areas: leg pain и stomach pain;
- answered reminders/questions: bowel movement, stomach medication, leg pain, ointment application;
- important observation: mild pain in left foot after waking up;
- notes: stomach tracking прошёл нормально, left-foot pain persists, pending questions больше нет.

Затем пользователь попросил остановить tracking для leg pain, потому что ноги больше не болят. Первый запрос вернул странный JSON-like ответ, похожий на runtime/tool-routing artifact PicoClaw. После повторного сообщения агент корректно деактивировал `leg_pain` target и подтвердил, что история сохранена.

Этот диалог показывает два важных результата:

1. Система умеет делать summary на основании backend state.
2. Система умеет управлять lifecycle tracking target: deactivate without deleting history.

Он также показывает ограничение PicoClaw runtime: иногда внешний агентный runtime может вернуть неожиданный внутренний вывод. Для production-версии было бы лучше писать собственный agent runner с полным контролем Telegram webhook, session state, tool routing и error handling.

Файл:

```text
report/dialog_5_summary_and_deactivation.md
```

---

## Репозиторий и структура

Проект содержит больше файлов, чем минимально требуется в задании, потому что реализует отдельный backend.

Основные части:

```text
src/                    backend source code
picoclaw_workspace/     AGENT.md, USER.md, SOUL.md, TOOLS.md, skills
picoclaw.example/       example PicoClaw config/security files
docs/                   architecture and design documentation
logs/                   mcp server and scheduler runtime logs
report/                 report and dialog files
data/                   SQLite database for local demo
scripts/                experimental scripts and model checks
```

Runtime обычно запускается двумя процессами:

```text
uv run health-api
picoclaw gateway
```

Первый процесс поднимает FastAPI/APScheduler backend. Второй запускает PicoClaw gateway и Telegram-facing agent.
