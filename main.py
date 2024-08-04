# main.py
import logging
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN

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
    /create_mailbox - Create a new mailbox
    /set_frequency - Set summary frequency for a mailbox
    /list_mailboxes - List your active mailboxes
    """
    await update.message.reply_text(help_text)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()


if __name__ == "__main__":
    main()
