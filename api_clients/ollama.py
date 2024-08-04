# api_clients/ollama.py
import aiohttp
from aiohttp import ClientTimeout
import logging
import asyncio
from config import OLLAMA_API_URL
import re


def clean_text(text):
    # Remove or replace problematic characters
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII characters
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces with single space
    text = re.sub(
        r"[^\w\s.,!?-]", "", text
    )  # Remove special characters except for some punctuation

    # Strip leading/trailing whitespace
    text = text.strip()

    # Optionally, you can limit the length of the text
    max_length = 10000  # Adjust as needed
    text = text[:max_length]

    return text


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_API_URL

    async def summarize_text(self, text):
        # Clean text from every character that could break the string and confuse the llm
        text = clean_text(text)
        print(f"Summarizing text: {text}")
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=600)) as session:
            try:
                print(f"Sending request to Ollama API: {self.base_url}/api/generate")
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "gemma2:2b",
                        "prompt": f"Please summarize the following text concisely:\n\n{text}",
                        "system": "You are a helpful AI assistant that summarizes newsletter content.",
                        "stream": False,
                    },
                ) as response:
                    print(
                        f"Received response from Ollama API. Status: {response.status}"
                    )
                    if response.status == 200:
                        data = await response.json()
                        print(f"Ollama response data: {data}")
                        return data.get("response", "")
                    else:
                        response_text = await response.text()
                        print(f"Ollama API error: {response.status} - {response_text}")
                        return None
            except asyncio.TimeoutError:
                print("Request to Ollama API timed out")
                return None
            except Exception as e:
                print(f"Error calling Ollama API: {str(e)}")
                import traceback

                print(f"Traceback: {traceback.format_exc()}")
                return None


ollama_client = OllamaClient()
logger.info("OllamaClient initialized")
