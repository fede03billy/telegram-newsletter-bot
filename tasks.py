# tasks.py
import logging
from database.models import get_session, Mailbox, User
from api_clients.mail_tm import mail_tm_client
from api_clients.ollama import ollama_client
from telegram.constants import ParseMode
import re


def format_for_telegram(text):
    # Escape special characters
    special_chars = "_*[]()~`>#+-=|{}.!"
    for char in special_chars:
        text = text.replace(char, f"\\{char}")

    # Replace markdown formatting with Telegram-compatible formatting
    text = re.sub(r"\\\*\\\*(.*?)\\\*\\\*", r"*\1*", text)  # Bold
    text = re.sub(r"\\\_(.*?)\\\_", r"_\1_", text)  # Italic
    text = text.replace("\\•", "•")  # Bullet points

    # Unescape periods within URLs
    text = re.sub(
        r"(\[.*?\]\()(.*?)(\\\.)(.*?)(\))",
        lambda m: f"{m.group(1)}{m.group(2)}.{m.group(4)}{m.group(5)}",
        text,
    )

    # Ensure proper line breaks
    paragraphs = text.split("\n\n")
    formatted_paragraphs = [p.replace("\n", " ").strip() for p in paragraphs]

    return "\n\n".join(formatted_paragraphs)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def fetch_emails_for_mailbox(mailbox):
    logger.info(f"Fetching unread emails for mailbox: {mailbox.email}")
    token = await mail_tm_client.get_token(mailbox.email, mailbox.password)
    if not token:
        logger.error(f"Failed to authenticate mailbox: {mailbox.email}")
        return []

    unread_messages = await mail_tm_client.fetch_unread_messages(token)
    logger.info(f"Fetched {len(unread_messages)} unread messages for {mailbox.email}")

    processed_messages = []
    for message in unread_messages:
        logger.debug(f"Processing unread message: {message}")

        content = message.get("text", message.get("html", ""))
        if not content:
            content = "No readable content found in this email."

        processed_messages.append(
            {
                "id": message.get("id"),
                "subject": message.get("subject", "No Subject"),
                "body": content,
            }
        )
        # Mark the message as read
        await mail_tm_client.mark_message_as_read(token, message["id"])

    logger.info(
        f"Processed {len(processed_messages)} unread messages for {mailbox.email}"
    )
    return processed_messages


async def summarize_emails(emails):
    print("Entering summarize_emails function")
    if not emails or not isinstance(emails, list):
        logger.info("No new emails to summarize.")
        return "No new emails to summarize."

    print(f"Number of emails to summarize: {len(emails)}")

    all_text = ""
    for email in emails:
        subject = email.get("subject", "No Subject")
        body = email.get("body", "No Content")
        all_text += f"Subject: {subject}\n\nContent:\n{body}\n\n---\n\n"

    try:
        print("About to call ollama_client.summarize_text")
        summary = await ollama_client.summarize_text(all_text)
        print(
            f"Received summary from Ollama (first 100 chars): {summary[:100] if summary else 'No summary generated'}..."
        )

        if summary:
            return f"Summary of {len(emails)} emails:\n\n{summary}"
        else:
            return (
                f"Failed to generate summary. Here are the subjects of the {len(emails)} new emails:\n\n"
                + "\n".join(
                    [f"- {email.get('subject', 'No Subject')}" for email in emails]
                )
            )
    except Exception as e:
        logger.error(f"Error in summarizing emails: {str(e)}")
        return (
            f"Error in summarizing emails. Here are the subjects of the {len(emails)} new emails:\n\n"
            + "\n".join([f"- {email.get('subject', 'No Subject')}" for email in emails])
        )


async def process_mailbox(mailbox):
    emails = await fetch_emails_for_mailbox(mailbox)
    if emails:
        summary = await summarize_emails(emails)
        # Here you would typically store this summary or send it to the user
        logger.info(f"Summary for {mailbox.email}: {summary}")


async def process_single_mailbox(bot, chat_id, mailbox_id):
    logger.info(f"Processing mailbox_id: {mailbox_id} for chat_id: {chat_id}")
    session = get_session()
    try:
        mailbox = session.query(Mailbox).get(mailbox_id)
        if not mailbox or str(mailbox.user.chat_id) != str(chat_id):
            logger.error(f"Mailbox not found or doesn't belong to user: {mailbox_id}")
            await bot.send_message(
                chat_id=chat_id,
                text="Mailbox not found or doesn't belong to you.",
            )
            return

        unread_emails = await fetch_emails_for_mailbox(mailbox)
        if unread_emails:
            summary = await summarize_emails(unread_emails)
            if summary:
                await send_summary(bot, chat_id, summary)
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Failed to generate summary for {mailbox.email}",
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=f"No new unread emails for {mailbox.email}",
            )

        mailbox.calculate_next_summary_time()
        session.commit()

    except Exception as e:
        logger.error(f"Error processing mailbox {mailbox_id}: {str(e)}")
        await bot.send_message(
            chat_id=chat_id,
            text=f"An error occurred while processing mailbox {mailbox.email}. Please try again later.",
        )
    finally:
        session.close()


async def process_user_mailboxes(context):
    user_id = context.job.data["user_id"]
    logger.info(f"Processing mailboxes for user_id: {user_id}")
    session = get_session()
    try:
        user = session.query(User).get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return

        for mailbox in user.mailboxes:
            await process_single_mailbox(context.bot, user.chat_id, mailbox.id)

        # Reschedule the job
        next_run = min((mb.next_summary_time for mb in user.mailboxes), default=None)
        if next_run:
            logger.info(f"Rescheduling summary job for user {user_id} at {next_run}")
            context.job_queue.run_once(
                process_user_mailboxes,
                when=next_run,
                data={"user_id": user_id},
                name=f"user_{user_id}_summary",
            )
    except Exception as e:
        logger.error(f"Error processing mailboxes for user {user_id}: {str(e)}")
    finally:
        session.close()


async def send_summary(bot, chat_id, summary):
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=format_for_telegram(summary),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        logger.info(f"Summary sent to chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error sending summary to chat_id {chat_id}: {str(e)}")
