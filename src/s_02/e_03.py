import json

import requests
from langfuse.decorators import observe, langfuse_context
from openai import OpenAI
import logging


class ImageGenerator:
    def __init__(self, api_key: str) -> None:
        """
        Initialize the ImageGenerator with OpenAI API key

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def scrape_website(self, url: str) -> str:
        """
        Scrape text content from a given URL

        Args:
            url (str): The URL to scrape

        Returns:
            str: The scraped text content
        """
        try:
            response = requests.get(url)
            response.raise_for_status()

            data = json.loads(response.text)

            # Extract description
            description = data.get("description", "")

            self.logger.info(f"Extracted description: {description}")

            return description

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error scraping website: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON: {e}")
            raise

    @observe(as_type="generation")
    def generate_image(self, prompt: str) -> str:
        """
        Generate image using DALL-E 3

        Args:
            prompt (str): The text prompt for image generation

        Returns:
            str: URL of the generated image
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            langfuse_context.update_current_observation(
                usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                }
            )

            self.logger.info("Done generating image")
            return response.data[0].url

        except Exception as e:
            self.logger.error(f"Error generating image: {e}")
            raise

    def process(self, url: str) -> str:
        """
        Main process: scrape website and generate image

        Args:
            url (str): The URL to scrape

        Returns:
            str: URL of the generated image
        """
        try:
            # Scrape website content
            self.logger.info(f"Scraping website: {url}")
            prompt = self.scrape_website(url)

            # Generate image from the scraped content
            self.logger.info("Generating image with DALL-E 3")
            image_url = self.generate_image(prompt)

            self.logger.info("Image generated successfully")
            return image_url

        except Exception as e:
            self.logger.error(f"Error processing: {e}")
            raise
