# main.py
import logging
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN
from database.models import get_session, User
from bot.commands import create_mailbox, list_mailboxes
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update, context):
    await update.message.reply_text(
        "Welcome to the Newsletter Bot! Use /help to see available commands."
    )


async def help_command(update, context):
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /create_mailbox <tag> - Create a new mailbox with the given tag
    /list_mailboxes - List your active mailboxes (up to 3)
    /set_frequency - Set summary frequency for a mailbox (Not implemented yet)
    """
    await update.message.reply_text(help_text)


def init_db():
    session = get_session()
    try:
        # Check if we can connect to the database
        session.execute(text("SELECT 1"))
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        session.close()


def main():
    logger.info("Starting the bot")

    init_db()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_mailbox", create_mailbox))
    application.add_handler(CommandHandler("list_mailboxes", list_mailboxes))

    logger.info("Bot is ready to accept commands")
    application.run_polling()


if __name__ == "__main__":
    main()
