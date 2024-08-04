# config.py
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
MAIL_TM_API_URL = os.getenv("MAIL_TM_API_URL", "https://api.mail.tm")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
