import os

import logging

from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from src.poligon import send

from src.s_01.e_05 import CensoredData, ModelProvider, check_ollama_status

load_dotenv()

langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)


@observe()
def main_anthropic():
    try:
        # Create instance using environment variables
        censor = CensoredData.from_env()

        key = os.environ.get("API_KEY")
        url_base = os.environ.get("CENTRALA_URL")

        if not all([key, url_base]):
            raise ValueError("Missing required environment variables")

        # Update Langfuse with initial context
        langfuse_context.update_current_observation(
            metadata={"url_base": url_base, "provider": "anthropic"}
        )

        # Process text
        input_url = f"{url_base}data/{key}/cenzura.txt"
        censored_text = censor.process_text(input_url)

        # Send result (assuming send function exists)
        endpoint = f"{url_base}report"
        res = send(endpoint, task="CENZURA", apikey=key, answer=censored_text)

        # Update Langfuse with final results
        langfuse_context.update_current_observation(
            metadata={
                "send_status": (
                    res.status_code if hasattr(res, "status_code") else "unknown"
                ),
                "completion_status": "success",
            }
        )

        print(res)

    except Exception as e:
        # Log error to Langfuse
        langfuse_context.update_current_observation(
            metadata={
                "error": str(e),
                "error_type": type(e).__name__,
                "completion_status": "error",
            }
        )
        logging.getLogger(__name__).error(f"Error in main: {str(e)}", exc_info=True)
        raise
    finally:
        langfuse.flush()


@observe()
def main_ollama():
    try:
        # Check if Ollama server is running
        if not check_ollama_status():
            error_msg = "Ollama server is not running. Please start it with 'ollama serve' in a separate terminal"
            langfuse_context.update_current_observation(
                metadata={
                    "error": error_msg,
                    "error_type": "RuntimeError",
                    "completion_status": "error",
                }
            )
            raise RuntimeError(error_msg)

        # Create instance using environment variables
        censor = CensoredData(
            provider=ModelProvider.OLLAMA, ollama_base_url="http://localhost:11434"
        )

        key = os.environ.get("API_KEY")
        url_base = os.environ.get("CENTRALA_URL")

        if not all([key, url_base]):
            raise ValueError("Missing required environment variables")

        # Update Langfuse with initial context
        langfuse_context.update_current_observation(
            metadata={
                "url_base": url_base,
                "provider": "ollama",
                "model": "llama3.1",
                "ollama_base_url": "http://localhost:11434",
            }
        )

        # Process text with llama3.1 model
        input_url = f"{url_base}data/{key}/cenzura.txt"
        censored_text = censor.process_text(input_url, model="llama3.1")

        # Send result
        endpoint = f"{url_base}report"
        res = send(endpoint, task="CENZURA", apikey=key, answer=censored_text)

        # Update Langfuse with final results
        langfuse_context.update_current_observation(
            metadata={
                "send_status": (
                    res.status_code if hasattr(res, "status_code") else "unknown"
                ),
                "completion_status": "success",
                "endpoint": endpoint,
            }
        )

        print(res)

    except Exception as e:
        # Log error to Langfuse
        langfuse_context.update_current_observation(
            metadata={
                "error": str(e),
                "error_type": type(e).__name__,
                "completion_status": "error",
            }
        )
        logging.getLogger(__name__).error(f"Error in main: {str(e)}", exc_info=True)
        raise
    finally:
        langfuse.flush()


if __name__ == "__main__":
    # change provider env var
    main_anthropic()
    # main_ollama()
