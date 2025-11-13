

# 🖥️ Server Control Bot
A secure Telegram bot for executing server-side commands, scripts, and maintenance routines remotely.

This tool was built to simplify administration of a large Ubuntu-based infrastructure, enabling safe execution of predefined commands without exposing direct SSH access to non-technical team members.

---

## ✨ Key Features

- 🔐 **Access Control (ACL)** — only approved Telegram users can run commands
- ⚙️ **Async subprocess execution** via `asyncio`
- 📏 **Output trimming** to stay within Telegram message size limits
- 🧹 **Execute maintenance scripts** (Python or Bash)
- 🖥️ **Remote orchestration** without direct SSH login
- 🧱 **Restricted command set** for secure operation
- 📝 Structured logging and error handling

---

## 📂 Project Structure

```
server_control_bot/
│
├── server_control_bot.py   # main bot logic
└── README.md               # this file
```

---

## 🚀 Usage

### 1. Install dependencies

```
pip install python-telegram-bot
```

### 2. Configure environment

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token_here
ALLOWED_USERS=123456789,987654321
``` 

Where `ALLOWED_USERS` is a comma-separated list of Telegram user IDs allowed to run commands.

---

## ▶️ Running the bot

```
python3 server_control_bot.py
```

The bot will start and listen for incoming commands.

---

## 🛠 How It Works

### 🔹 Access Control
- The bot checks the sender's Telegram ID.
- Only users listed in `ALLOWED_USERS` can run commands.
- Unauthorized attempts are logged and ignored.

### 🔹 Running Commands
- Uses `asyncio.create_subprocess_exec()` for non-blocking execution.
- Captures both stdout and stderr.
- Trims long output to avoid Telegram's 4096-character limit.

### 🔹 Supported Operations
- Running Python scripts
- Executing `.sh` shell scripts
- Running maintenance commands (example: `df -h`, `htop` snapshots, cleanup tasks)
- Fetching server info (uptime, disk usage, logs)

> **Important:** The bot works only with the predefined list of allowed commands for safety.

---

## 🧱 Example Command Flow

User sends:
```
/run uptime
```

Bot replies:
```
Server uptime:
 14:22:51 up 12 days,  5:41,  load average: 0.20, 0.31, 0.27
```

Another example:
```
/run backup_script
```
Bot:
```
Running backup...
Backup completed successfully.
```

---

## 🔐 Security Considerations

- SSH access is **not** exposed; bot handles execution internally.
- Commands are restricted to a predefined safe list.
- Outputs are automatically sanitized and limited in size.
- Users must be explicitly whitelisted.

---

## 🛠 Tech Stack

- Python 3
- python-telegram-bot
- asyncio
- subprocess
- dotenv (optional)

---

## 💡 Practical Use Cases

- Managing a remote storage server (e.g., 120TB RAID6 setup)
- Running routine scripts without SSH access
- Quick incident handling (restart services, check logs, run cleaners)
- Empower non-technical teammates to trigger safe actions

---

## 📄 License
MIT License