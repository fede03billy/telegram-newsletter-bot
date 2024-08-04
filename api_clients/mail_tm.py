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
                f"{self.base_url}/messages?page=1&isDeleted=false&seen=false"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = data["hydra:member"]
                    logger.debug(f"Received messages data: {data}")
                    full_messages = []
                    for message in messages:
                        # Fetch full message content
                        async with session.get(
                            f"{self.base_url}/messages/{message['id']}"
                        ) as msg_response:
                            if msg_response.status == 200:
                                full_message = await msg_response.json()
                                logger.debug(f"Full message data: {full_message}")
                                full_messages.append(full_message)
                            else:
                                logger.error(
                                    f"Failed to fetch full message: {message['id']}"
                                )
                    return full_messages
                else:
                    logger.error(f"Failed to fetch messages. Status: {response.status}")
                    return []

    async def mark_message_as_read(self, token, message_id):
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.patch(
                f"{self.base_url}/messages/{message_id}", json={"seen": True}
            ) as response:
                if response.status == 200:
                    logger.info(f"Marked message {message_id} as read")
                    return True
                else:
                    logger.error(
                        f"Failed to mark message {message_id} as read. Status: {response.status}"
                    )
                    return False


mail_tm_client = MailTMClient()
