# api_clients/ollama.py
import aiohttp
from aiohttp import ClientTimeout
import logging
import asyncio
from config import OLLAMA_API_URL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_API_URL

    async def summarize_text(self, text):
        logger.debug(f"Summarizing text (first 1000 chars): {text[:1000]}...")
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=600)) as session:
            try:
                logger.debug(
                    f"Sending request to Ollama API: {self.base_url}/api/generate"
                )
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "phi3:3.8b",
                        "prompt": f"Please summarize the following text concisely:\n\n{text}",
                        "system": "You are a helpful AI assistant that summarizes newsletter content.",
                        "stream": False,
                    },
                ) as response:
                    logger.debug(
                        f"Received response from Ollama API. Status: {response.status}"
                    )
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Ollama response data: {data}")
                        return data.get("response", "")
                    else:
                        response_text = await response.text()
                        logger.error(
                            f"Ollama API error: {response.status} - {response_text}"
                        )
                        return None
            except asyncio.TimeoutError:
                logger.error("Request to Ollama API timed out")
                return None
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                return None


ollama_client = OllamaClient()
logger.info("OllamaClient initialized")
