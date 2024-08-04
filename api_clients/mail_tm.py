# api_clients/mail_tm.py
import aiohttp
from config import MAIL_TM_API_URL
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MailTMClient:
    def __init__(self):
        self.base_url = MAIL_TM_API_URL

    async def get_domains(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/domains") as response:
                if response.status == 200:
                    data = await response.json()
                    return data["hydra:member"]
                else:
                    return None

    async def create_account(self, address, password):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/accounts",
                json={"address": address, "password": password},
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    return data
                else:
                    return None

    async def get_token(self, address, password):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/token",
                json={"address": address, "password": password},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["token"]
                else:
                    return None

    async def fetch_unread_messages(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                f"{self.base_url}/messages?page=1&isDeleted=false"
            ) as response:
                if response.status == 200:
                    print("Fetching messages...")
                    print(f"message response: {response}")
                    data = await response.json()
                    all_messages = data["hydra:member"]
                    print(f"Received messages data: {data}")

                    # Filter unread messages
                    unread_messages = [
                        msg for msg in all_messages if msg.get("seen") == False
                    ]
                    print(f"Number of unread messages: {len(unread_messages)}")

                    full_messages = []
                    for message in unread_messages:
                        # Fetch full message content
                        async with session.get(
                            f"{self.base_url}/messages/{message['id']}"
                        ) as msg_response:
                            if msg_response.status == 200:
                                full_message = await msg_response.json()
                                print(f"Full unread message data: {full_message}")
                                full_messages.append(full_message)
                            else:
                                logger.error(
                                    f"Failed to fetch full unread message: {message['id']}"
                                )
                    return full_messages
                else:
                    logger.error(f"Failed to fetch messages. Status: {response.status}")
                    return []

    async def mark_message_as_read(self, token, message_id):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/merge-patch+json",  # This is the key change
        }
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/messages/{message_id}",
                headers=headers,
                json={"seen": True},
            ) as response:
                if response.status == 200:
                    logger.info(f"Marked message {message_id} as read")
                    return True
                else:
                    response_text = await response.text()
                    logger.error(
                        f"Failed to mark message {message_id} as read. Status: {response.status}, Response: {response_text}"
                    )
                    return False


mail_tm_client = MailTMClient()
