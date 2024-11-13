import os

import logging

import requests
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe

from src.poligon import send

from src.s_01.e_05 import CensoredData, ModelProvider

load_dotenv()

langfuse = Langfuse(
    secret_key=os.environ["S01E05_LANGFUSE_SECRET_KEY"],
    public_key=os.environ["S01E05_LANGFUSE_PUBLIC_KEY"],
    host=os.environ["S01E05_LANGFUSE_HOST"],
)


def check_ollama_status():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/version")
        return response.status_code == 200
    except requests.RequestException:
        return False


@observe()
def main_anthropic():
    try:
        # Create instance using environment variables
        censor = CensoredData.from_env()

        key = os.environ.get("API_KEY")
        url_base = os.environ.get("CENTRALA_URL")

        if not all([key, url_base]):
            raise ValueError("Missing required environment variables")

        # Process text
        input_url = f"{url_base}data/{key}/cenzura.txt"
        censored_text = censor.process_text(input_url)

        # Send result (assuming send function exists)
        endpoint = f"{url_base}report"
        res = send(endpoint, task="CENZURA", apikey=key, answer=censored_text)
        print(res)

    except Exception as e:
        logging.getLogger(__name__).error(f"Error in main: {str(e)}", exc_info=True)
        raise


@observe()
def main_ollama():
    try:
        # Check if Ollama server is running
        if not check_ollama_status():
            raise RuntimeError(
                "Ollama server is not running. Please start it with 'ollama serve' in a separate terminal"
            )

        # Create instance using environment variables
        censor = CensoredData(
            provider=ModelProvider.OLLAMA, ollama_base_url="http://localhost:11434"
        )

        key = os.environ.get("API_KEY")
        url_base = os.environ.get("CENTRALA_URL")

        if not all([key, url_base]):
            raise ValueError("Missing required environment variables")

        # Process text with llama3.1 model
        input_url = f"{url_base}data/{key}/cenzura.txt"
        censored_text = censor.process_text(input_url, model="llama3.1")

        # Send result
        endpoint = f"{url_base}report"
        res = send(endpoint, task="CENZURA", apikey=key, answer=censored_text)
        print(res)

    except Exception as e:
        logging.getLogger(__name__).error(f"Error in main: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # change provider env var
    main_anthropic()
    # main_ollama()
