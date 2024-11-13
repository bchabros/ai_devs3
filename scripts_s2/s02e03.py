import os

from dotenv import load_dotenv

from src.logger import logger
from src.s_02.e_03 import ImageGenerator
from src.poligon import send

load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]
api_key = os.environ["API_KEY"]
main_url = os.environ["CENTRALA_URL"]
endpoint = f"{os.environ.get('CENTRALA_URL')}report"

url=f"{main_url}data/{api_key}/robotid.json"

generator = ImageGenerator(openai_api_key)

try:
    image_url = generator.process(url)
    logger.info(f"Generated image URL: {image_url}")
except Exception as e:
    logger.info(f"An error occurred: {e}")

res = send(endpoint, task="robotid", apikey=api_key, answer=image_url)
print(res)
