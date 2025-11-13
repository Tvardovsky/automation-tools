

# 📨 Telegram Support Bot
A lightweight internal task and ticket management system built on top of Telegram.

This bot was designed to streamline communication between content managers and technical staff by replacing scattered messages with a structured ticket workflow. It supports task creation, file attachments, status changes, and manager notifications — all from within Telegram.

---

## ✨ Key Features

- 📝 **Create tasks** with descriptions, categories, and optional file attachments
- 📎 **Save and store files** (audio, images, documents) linked to each task
- 🔄 **Task status workflow:**
  - `Open` → `In Progress` → `Done`
- 🗂 **SQLite database** for persistent storage
- 🔔 **Manager notifications** for new tasks or updates
- 🔘 **Inline keyboards** for user-friendly navigation
- 👤 **User-specific filtering:** view only your tasks, completed tasks, active tasks
- 🧩 Built as a standalone ticketing system requiring no external services

---

## 📂 Project Structure

```
telegram_support_bot/
│
├── telegrambot_support.py   # main bot implementation
└── README.md                # this file
```

---

## 🚀 Usage

### 1. Install dependencies

```
pip install python-telegram-bot
```

If you use `.env` for configuration:
```
pip install python-dotenv
```

### 2. Set environment variables

Create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your_token_here
MANAGER_CHAT_ID=123456789
```

---

## ▶️ Running the bot

```
python3 telegrambot_support.py
```

The bot will start polling for new updates.

---

## 🧠 How It Works

### 🔹 Task Creation
- User sends `/newtask`
- Bot asks for task description
- User optionally uploads files
- Task is saved to SQLite database
- Manager receives a notification

### 🔹 Task Management
Users and managers can:
- Change task status (`Open`, `In Progress`, `Done`)
- Add comments or attachments
- View all tasks or only personal tasks
- View completed history

### 🔹 Database
SQLite tables typically include:
- `tasks` — id, user_id, description, status, timestamp
- `attachments` — file paths linked to task_id
- `comments` — notes, timestamps

Database schema automatically migrates on startup if fields are missing.

---

## 🧱 Example Message Flow

**User:** `/newtask`
```
Please describe the task.
```
**User:**
```
Remove duplicate releases from FUGA batch.
```
**Bot:**
```
Task created and sent to manager.
```

Manager receives:
```
New task from @username
Description: Remove duplicate releases from FUGA batch.
```

---

## 🛠 Tech Stack

- Python 3
- python-telegram-bot
- SQLite
- dotenv (optional)
- file handling utilities (`os`, `pathlib`, etc.)

---

## 💡 Practical Use Cases

- Internal communication for content distribution workflows
- Managing editing tasks, metadata corrections, and daily operations
- Tracking requests from specific clients
- Replacing chaotic message threads with structured tasks

---

## 📄 License
MIT License