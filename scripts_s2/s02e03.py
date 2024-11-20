import os

from dotenv import load_dotenv
from langfuse import Langfuse

from src.logger import logger
from src.s_02.e_03 import ImageGenerator
from src.send_task import send

load_dotenv()

langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)

openai_api_key = os.environ["OPENAI_API_KEY"]
api_key = os.environ["API_KEY"]
main_url = os.environ["CENTRALA_URL"]
endpoint = f"{os.environ.get('CENTRALA_URL')}report"

url = f"{main_url}data/{api_key}/robotid.json"


def main():
    generator = ImageGenerator(openai_api_key)

    try:
        image_url = generator.process(url)
        logger.info(f"Generated image URL: {image_url}")
    except Exception as e:
        logger.info(f"An error occurred: {e}")

    res = send(endpoint, task="robotid", apikey=api_key, answer=image_url)
    print(res)


if __name__ == "__main__":

    main()
