# api_clients/mail_tm.py
import aiohttp
from config import MAIL_TM_API_URL


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


mail_tm_client = MailTMClient()
