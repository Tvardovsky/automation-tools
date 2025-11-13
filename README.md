# ⚙️ automation-tools  
A collection of Python automation utilities for data pipelines, XML/CSV processing, Telegram bots, API integrations and server orchestration.

This repository contains production-ready tools developed for large-scale digital content workflows:

- DDEX XML processing  
- Metadata validation  
- Cover art upscaling  
- Telegram bots for task management  
- API tools for Spotify / Apple Music  
- Remote server orchestration  
- Data pipelines for catalogs (1M+ rows)  
- Automation of repetitive B2B workflows  

All tools were built for real business scenarios: large catalog ingestion, metadata cleanup, automation of internal operations, task tracking and server maintenance.

---

## 📂 Repository Structure

```
automation-tools/
│
├── ddex_converter/
│ ├── local_ddex_packages_converter.py
│ └── README.md
│
├── artistid_bot/
│ ├── artistid.py
│ ├── spotify_check.py
│ └── README.md
│
├── telegram_support_bot/
│ ├── telegrambot_support.py
│ └── README.md
│
├── server_control_bot/
│ ├── server_control_bot.py
│ └── README.md
│
└── README.md <-- (this file)
```

---

## 🚀 Projects Overview

### **1. DDEX Converter (XML/Images/MD5 Automation)**  
Full pipeline for processing DDEX 3.8.2 packages:

- XML parsing (lxml)  
- Cover art upscaling to **3000×3000 px**  
- MD5 recalculation  
- Batch generation  
- Namespace/header fixes  

👉 Located in: **`/ddex_converter`**

---

### **2. ArtistID Finder for Spotify/Apple (Telegram Bot + API Tool)**  
Fast lookup of artist profiles via APIs with fuzzy matching.  

👉 Located in: **`/artistid_bot`**

---

### **3. Telegram Support Bot (Task Tracker)**  
Internal mini ticketing system for daily content tasks.  

👉 Located in: **`/telegram_support_bot`**

---

### **4. Server Control Bot (Remote Orchestration)**  
Runs secure server-side commands using ACL and asyncio.  

👉 Located in: **`/server_control_bot`**

---

## 🛠 Tech Stack

**Python:** Pandas, lxml, Pillow, asyncio, sqlite3, requests  
**Bots:** python-telegram-bot  
**Infrastructure:** Ubuntu Server, RAID6, CrushFTP, Docker (basic), cron  
**APIs:** Spotify API, Apple iTunes Search  
**Formats:** XML (DDEX, FUGA), CSV, JSON  
**Tools:** Git, Postman  

---

## 📄 License  
MIT License