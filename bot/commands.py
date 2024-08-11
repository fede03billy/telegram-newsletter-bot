# bot/commands.py
import logging
import secrets
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
)
from database.models import get_session, User, Mailbox, SummaryFrequency
from api_clients.mail_tm import mail_tm_client
from tasks import process_single_mailbox

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
                mailbox = Mailbox(email=email, password=password, tag=tag, user=user)
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


# Define conversation states
SELECTING_MAILBOX, SELECTING_FREQUENCY = range(2)


async def set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.debug(f"Received set_frequency command. Chat ID: {chat_id}")

    session = get_session()
    try:
        user = session.query(User).filter_by(chat_id=str(chat_id)).first()
        if not user or not user.mailboxes:
            await update.message.reply_text(
                "You don't have any mailboxes yet. Use /create_mailbox to create one."
            )
            return ConversationHandler.END

        mailboxes = user.mailboxes[:3]  # Limit to 3 mailboxes
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{mb.email} ({mb.tag})", callback_data=f"mailbox:{mb.id}"
                )
            ]
            for mb in mailboxes
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Select a mailbox to set frequency:", reply_markup=reply_markup
        )
        return SELECTING_MAILBOX
    except Exception as e:
        logger.exception("An error occurred while setting frequency")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END
    finally:
        session.close()


async def mailbox_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mailbox_id = query.data.split(":")[1]
    context.user_data["selected_mailbox"] = mailbox_id

    keyboard = [
        [InlineKeyboardButton("Daily", callback_data="freq:daily")],
        [InlineKeyboardButton("Weekly", callback_data="freq:weekly")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Select summary frequency:", reply_markup=reply_markup
    )
    return SELECTING_FREQUENCY


async def frequency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    frequency = query.data.split(":")[1]
    mailbox_id = context.user_data["selected_mailbox"]

    session = get_session()
    try:
        mailbox = session.query(Mailbox).filter_by(id=mailbox_id).first()
        if mailbox:
            mailbox.summary_frequency = SummaryFrequency[frequency.upper()]
            session.commit()

            # Schedule or reschedule the job for this user
            user = mailbox.user
            next_run = min(mb.next_summary_time for mb in user.mailboxes)
            context.job_queue.run_once(
                process_user_mailbox,
                when=next_run,
                data={"user_id": user.id},
                name=f"user_{user.id}_summary",
            )

            await query.edit_message_text(
                f"Frequency for mailbox {mailbox.email} set to {frequency}."
            )
        else:
            await query.edit_message_text("Mailbox not found. Please try again.")
    except Exception as e:
        logger.exception("An error occurred while setting frequency")
        await query.edit_message_text("An error occurred. Please try again later.")
    finally:
        session.close()
    return ConversationHandler.END


set_frequency_handler = ConversationHandler(
    entry_points=[CommandHandler("set_frequency", set_frequency)],
    states={
        SELECTING_MAILBOX: [
            CallbackQueryHandler(mailbox_selected, pattern=r"^mailbox:")
        ],
        SELECTING_FREQUENCY: [
            CallbackQueryHandler(frequency_selected, pattern=r"^freq:")
        ],
    },
    fallbacks=[],
    per_message=False,
)

# Define a new state for mailbox selection
SELECTING_MAILBOX_FOR_SUMMARY = 1


async def trigger_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Triggering summary for chat_id: {chat_id}")
    session = get_session()
    try:
        user = session.query(User).filter_by(chat_id=str(chat_id)).first()
        if not user or not user.mailboxes:
            await update.message.reply_text("You don't have any mailboxes set up.")
            return ConversationHandler.END

        if len(user.mailboxes) == 1:
            # If there's only one mailbox, process it directly
            mailbox = user.mailboxes[0]
            await process_single_mailbox(context.bot, chat_id, mailbox.id)
            return ConversationHandler.END

        # If there are multiple mailboxes, let the user choose
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{mb.email} ({mb.tag})", callback_data=f"summary:{mb.id}"
                )
            ]
            for mb in user.mailboxes
        ]
        keyboard.append(
            [InlineKeyboardButton("All Mailboxes", callback_data="summary:all")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Select a mailbox to summarize:", reply_markup=reply_markup
        )
        return SELECTING_MAILBOX_FOR_SUMMARY

    except Exception as e:
        logger.error(f"Error in trigger_summary: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END
    finally:
        session.close()


async def mailbox_selected_for_summary(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    selection = query.data.split(":")[1]

    if selection == "all":
        session = get_session()
        try:
            user = session.query(User).filter_by(chat_id=str(chat_id)).first()
            for mailbox in user.mailboxes:
                await process_single_mailbox(context.bot, chat_id, mailbox.id)
        finally:
            session.close()
    else:
        mailbox_id = int(selection)
        await process_single_mailbox(context.bot, chat_id, mailbox_id)

    await query.edit_message_text("Summary process completed.")
    return ConversationHandler.END


trigger_summary_handler = ConversationHandler(
    entry_points=[CommandHandler("trigger_summary", trigger_summary)],
    states={
        SELECTING_MAILBOX_FOR_SUMMARY: [
            CallbackQueryHandler(mailbox_selected_for_summary, pattern=r"^summary:")
        ],
    },
    fallbacks=[],
)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END
