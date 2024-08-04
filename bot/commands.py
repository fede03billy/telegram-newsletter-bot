# bot/commands.py
import logging
import secrets
import string
from telegram import Update
from telegram.ext import ContextTypes
from database.models import get_session, User, Mailbox
from api_clients.mail_tm import mail_tm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(length))


async def create_mailbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tag = context.args[0] if context.args else None

    logger.debug(f"Received create_mailbox command. Chat ID: {chat_id}, Tag: {tag}")

    if not tag:
        await update.message.reply_text(
            "Please provide a tag for the mailbox. Usage: /create_mailbox <tag>"
        )
        return

    session = get_session()
    try:
        user = session.query(User).filter_by(chat_id=str(chat_id)).first()
        if not user:
            user = User(chat_id=str(chat_id))
            session.add(user)
            session.commit()

        if len(user.mailboxes) >= 3:
            await update.message.reply_text(
                "You can only have up to 3 active mailboxes."
            )
            return

        domains = await mail_tm_client.get_domains()
        if not domains:
            await update.message.reply_text(
                "Failed to fetch available domains. Please try again later."
            )
            return

        username = "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10)
        )
        email = f"{username}@{domains[0]['domain']}"
        password = generate_password()

        account = await mail_tm_client.create_account(email, password)
        if account:
            token = await mail_tm_client.get_token(email, password)
            if token:
                mailbox = Mailbox(email=email, tag=tag, user=user)
                session.add(mailbox)
                session.commit()
                await update.message.reply_text(
                    f"Mailbox created successfully:\nEmail: {email}\nPassword: {password}\nPlease save these credentials securely."
                )
            else:
                await update.message.reply_text(
                    "Failed to authenticate the new mailbox. Please try again later."
                )
        else:
            await update.message.reply_text(
                "Failed to create mailbox. Please try again later."
            )
    except Exception as e:
        await update.message.reply_text("An error occurred while creating the mailbox.")
        print(f"Error: {e}")
    finally:
        session.close()


async def list_mailboxes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.debug(f"Received list_mailboxes command. Chat ID: {chat_id}")

    session = get_session()
    try:
        user = session.query(User).filter_by(chat_id=str(chat_id)).first()
        if not user:
            await update.message.reply_text(
                "You don't have any mailboxes yet. Use /create_mailbox to create one."
            )
            return

        mailboxes = user.mailboxes[:3]  # Limit to 3 mailboxes
        if not mailboxes:
            await update.message.reply_text(
                "You don't have any mailboxes yet. Use /create_mailbox to create one."
            )
        else:
            mailbox_list = "\n".join(
                [
                    f"Email: {mb.email}, Tag: {mb.tag}, Frequency: {mb.summary_frequency}"
                    for mb in mailboxes
                ]
            )
            await update.message.reply_text(f"Your mailboxes:\n\n{mailbox_list}")
    except Exception as e:
        logger.exception("An error occurred while listing mailboxes")
        await update.message.reply_text(
            "An error occurred while listing your mailboxes. Please try again later."
        )
    finally:
        session.close()
