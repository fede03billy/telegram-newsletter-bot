# api_clients/ollama.py
import aiohttp
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from config import OLLAMA_API_URL


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def chunk_text(text, max_chunk_size=8000):
    chunks = []
    current_chunk = ""
    for sentence in text.split("."):
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + "."
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


class OllamaClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.max_chunk_size = 8000

    async def summarize_text(self, text):
        return await self._recursive_summarize([text])

    async def _recursive_summarize(self, chunks):
        print(f"Chunks to summarize: {len(chunks)}")
        if len(chunks) == 1 and len(chunks[0]) <= self.max_chunk_size:
            return await self._generate_final_summary(chunks[0])

        summaries = []
        for chunk in chunks:
            summary = await self._generate_summary(chunk)
            summaries.append(summary)
            print(
                f"Summary generated: {summary[:100]}..."
            )  # Print first 100 chars of each summary

        combined_summary = " ".join(summaries)
        if len(combined_summary) <= self.max_chunk_size:
            return await self._generate_final_summary(combined_summary)
        else:
            return await self._recursive_summarize(chunk_text(combined_summary))

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_summary(self, chunk):
        prompt = f"""Summarize this newsletter chunk comprehensively:

            {chunk}

            Include:
            - All main topics/headlines
            - Key points for each topic (no omissions)
            - Important dates, events, figures
            - Newsletter name and relevant links

            Format: 
            - Use bullet points or short paragraphs
            - Simplify language, but keep all core concepts
            - No length limit, focus on completeness
        """

        return await self._make_api_call(prompt)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_final_summary(self, text):
        prompt = f"""Create detailed Telegram newsletter summary:

            {text}

            - Include all main topics and key points
            - Organize by sections or themes
            - Use short paragraphs (2-3 sentences each)
            - Highlight important dates/events
            - Mention newsletter name and any provided links
            - No word limit, but aim for clarity and readability

        """

        return await self._make_api_call(prompt)

    async def _make_api_call(self, prompt):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "gemma2:2b",
                    "prompt": prompt,
                    "system": "You are a helpful AI assistant that summarizes newsletter content.",
                    "stream": False,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "")
                else:
                    raise Exception(f"API call failed with status {response.status}")


ollama_client = OllamaClient(OLLAMA_API_URL)
logger.info("OllamaClient initialized")
