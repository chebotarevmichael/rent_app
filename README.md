
# Marketing Events & Messaging Pipeline (Test Assignment)

## 🇬🇧 English language

### Problem Description

This service simulates a marketing event pipeline for a fintech application.

The system:
1. Accepts user behavioral events via HTTP.
2. Applies declarative messaging rules.
3. Prevents duplicate or excessive messages.
4. Produces outbound send requests (stubbed).
5. Exposes an audit/debug endpoint to explain decisions.

The goal is to demonstrate clean modeling, idempotency, deduplication, and auditability.

---

### Supported Event Types

- signup_completed
- link_bank_success
- payment_initiated
- payment_failed

---

### Implemented Messaging Rules

1. WELCOME_EMAIL
 Trigger: signup_completed
 Condition: marketing_opt_in == true
 Limit: once per user

2. BANK_LINK_NUDGE_SMS
 Trigger: link_bank_success
 Condition: within 24h after signup_completed

3. INSUFFICIENT_FUNDS_EMAIL
 Trigger: payment_failed
 Condition: failure_reason == INSUFFICIENT_FUNDS
 Limit: once per user per calendar day

4. HIGH_RISK_ALERT (internal)
 Trigger: payment_failed
 Condition: attempt_number >= 3
 Output: logs only

---

### API

POST /events
GET /audit/{user_id}

---

### MVP Constraints

- In-memory only
- Single process
- UTC everywhere
- No auth, queues, retries, metrics
- Rules defined in code
- Deduplication by user_id + template (+ day)
- HIGH_RISK_ALERT logged only

---

## 🇷🇺 Русский язык

### Описание самого кода и пакетов
❗️[тут](https://github.com/chebotarevmichael/rent_app/tree/main/src)

### Описание задачи

Сервис моделирует маркетинговый pipeline событий для финтех-приложения.

Система:
1. Принимает события по HTTP
2. Применяет правила
3. Делает дедупликацию
4. Формирует outbound-запросы
5. Даёт audit/debug API

---

### Поддерживаемые события

- signup_completed
- link_bank_success
- payment_initiated
- payment_failed

---

### Правила

- WELCOME_EMAIL — при signup_completed и marketing_opt_in
- BANK_LINK_NUDGE_SMS — link_bank_success в течение 24ч
- INSUFFICIENT_FUNDS_EMAIL — 1 раз в день
- HIGH_RISK_ALERT — attempt_number >= 3, только лог

---

### Ограничения MVP

- Всё в памяти
- Один процесс
- UTC
- Без auth и очередей
- Правила только в коде
