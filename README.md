# 🎟️ Discord Ticket Bot

Developed by: ZeonXq (zeon.sls)
A full-featured, modern **ticket system bot** for Discord using `discord.py` with **slash commands only**.

---

## ✨ Features

- `/ticket-setup`: Creates ticket category, ticket & log channels
- `/ticket-admin <role>`: Adds a ticket admin role
- `/ticket-remove-admin <role>`: Removes a ticket admin role
- `/ticket-message <channel> <content> <button_label>`: Sends an embed + ticket button
- 🎫 Users can open tickets with a button
- 🔒 Ticket can be closed by anyone, hiding it from the user
- 🗑️ Admins can delete the ticket (with full transcript logging)
- 🔁 Admins can reopen closed tickets
- 📁 Transcript is generated in `.txt` format and sent to:
  - The ticket creator via DM
  - The `ticket-log` channel

---

## 🛠️ Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ZeonXq/discord-ticket_bot.git
   cd TicketBot

   pip install -r requirements.txt
   update the .env file

   Run the bot:
   python bot.py

## Folder Structure
```bash
ticket-bot/
├── bot.py
├── cogs/
│   └── ticket.py
├── utils/
│   └── transcript.py
├── data/
│   └── config.json
├── transcripts/
├── requirements.txt
└── README.md
