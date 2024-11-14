import os
import asyncio
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe

from src.s_02.e_04 import ContentClassifier
from src.poligon import send

load_dotenv()
langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)


@observe()
async def main():

    endpoint = f"{os.environ['CENTRALA_URL']}report"
    api_key = os.environ["API_KEY"]

    classifier = ContentClassifier(
        claude_api_key=os.environ["ANTHROPIC_API_KEY"],
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )

    results = await classifier.classify_folder(
        "/Users/bha/Documents/project/ai_devs/pliki_z_fabryki"
    )
    print(results)

    res = send(endpoint, task="kategorie", apikey=api_key, answer=results)
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
