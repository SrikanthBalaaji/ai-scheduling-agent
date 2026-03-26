# AI Scheduling Agent — Project Plan

## 🧠 Current State (as of now)

### Backend

* FastAPI server is running
* `/events` endpoint exists (static data)
* `/chat` endpoint exists (basic agent logic)
* Basic folder structure created:

  * backend/routes
  * backend/agent
  * backend/db

### Agent

* Simple rule-based agent implemented
* Can:

  * respond to user input
  * simulate scheduling decisions

### GitHub

* Repo initialized and synced
* Initial structure pushed to main branch

---

## 🎯 Project Goal

Build an AI-powered student planner with:

1. Event Billboard (college events)
2. Personal Calendar (user schedule)
3. AI Agent (decision making + recommendations)

---

## 👥 Team Roles

### Person A — Events System

* Manage event data
* Build `/events` API
* Add filtering and categories

---

### Person B — Calendar System

* Manage user schedule
* Build `/calendar` API
* Handle personal events

---

### Person C — Agent (YOU)

* Build decision logic
* Detect conflicts
* Recommend events
* Maintain `/chat` endpoint

---

### Person D — Frontend

* Build UI (React)
* Display events
* Chat interface
* Planner view

---

## 🔗 Integration Rules (VERY IMPORTANT)

### APIs to use:

* `/events`
* `/calendar`
* `/chat`

---

### Event Format (DO NOT CHANGE)

```json
{
  "id": "string",
  "title": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "tags": []
}
```

---

### Calendar Format (DO NOT CHANGE)

```json
{
  "title": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "type": "personal/event"
}
```

---

### Agent Response Format (DO NOT CHANGE)

```json
{
  "reply": "string",
  "action": "string",
  "recommended_event": {}
}
```

---

## 🛠️ Immediate Next Steps

### Person A

* Move events to database
* Add filtering (by date, category)

---

### Person B

* Create calendar storage
* Add API to insert events

---

### Person C (YOU)

* Improve conflict detection
* Add recommendation logic

---

### Person D

* Create basic UI (event list + chat)

---

## ⚠️ Rules

* Do NOT change API formats without informing team
* Do NOT overwrite other modules
* Keep implementation simple (hackathon scope)

---

## 🚀 Branching Strategy

* `main` → stable code
* `dev` → active development
* feature branches per person

---

## 📌 Notes

* Folder structure is flexible
* Focus on integration, not perfection
* Goal is working demo, not production system
