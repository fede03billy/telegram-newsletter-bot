# Telegram Newsletter Bot

A bot that creates temporary email addresses, fetches newsletters, and provides complete summaries directly in Telegram.

## Features

- Create temporary email addresses (up to 3 per user)
- Automatically fetch and process incoming emails
- Generate summaries of newsletter content using AI
- Customizable summary frequency (daily or weekly)

## Tech Stack

- **Python 3.12**
- **python-telegram-bot**: For Telegram bot functionality
- **SQLAlchemy**: ORM for database operations
- **aiohttp**: Asynchronous HTTP client for API requests
- **Mail.tm API**: For temporary email creation and management
- **Ollama API**: For AI-powered text summarization

## Project Structure

```
copytelegram_newsletter_bot/
├── bot/
│   ├── __init__.py
│   ├── handlers.py
│   └── commands.py
├── database/
│   ├── __init__.py
│   └── models.py
├── api_clients/
│   ├── __init__.py
│   ├── mail_tm.py
│   └── ollama.py
├── config.py
├── main.py
├── tasks.py
└── requirements.txt
```

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/telegram-newsletter-bot.git
   cd telegram-newsletter-bot
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=sqlite:///bot.db
   MAIL_TM_API_URL=https://api.mail.tm
   OLLAMA_API_URL=http://localhost:11434
   ```

5. Run the bot:
   ```
   python main.py
   ```

## Usage

1. Start a chat with your bot on Telegram
2. Use `/start` to initialize the bot
3. Create a mailbox using `/create_mailbox <tag>`
4. Set summary frequency with `/set_frequency`
5. Use `/list_mailboxes` to view your active mailboxes
6. Trigger immediate summaries with `/trigger_summary`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Mail.tm](https://mail.tm/)
- [Ollama](https://ollama.ai/)
