import base64
import logging
import os
from collections import Counter
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from typing import Dict, Tuple, List, Literal

from src.prompt.s02e02 import IMAGE_PROMPT

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simpler_logger")


class CityImageAnalyzer:
    """Class for analyzing city images using different AI models"""

    PROMPT = IMAGE_PROMPT

    def __init__(self, image_folder: str):
        """Initialize the analyzer with image folder path and load environment variables"""
        load_dotenv()
        self.image_folder = image_folder
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.results = {}

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encode image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_image_anthropic(self, image_path: str) -> str:
        """Analyze a single image using Claude"""
        base64_image = self.encode_image(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.PROMPT},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    },
                ],
            }
        ]
        logger.info(f"Analyzing image with Claude {format(image_path)}")
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=messages,
        )
        logger.info(f"Claude response: {response.content[0].text}")
        return response.content[0].text

    def analyze_image_openai(self, image_path: str) -> str:
        """Analyze image using GPT-4"""
        base64_image = self.encode_image(image_path)
        logger.info(f"Analyzing image with GPT: {image_path}")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=100,
        )
        logger.info(f"GPT response: {response.choices[0].message.content.strip()}")
        return response.choices[0].message.content.strip()

    def analyze_all_images(
        self, model_type: Literal["anthropic", "openai"]
    ) -> Dict[str, str]:
        """Analyze all PNG images in the folder using specified model"""
        results = {}
        analyze_func = (
            self.analyze_image_anthropic
            if model_type == "anthropic"
            else self.analyze_image_openai
        )

        image_files = list(Path(self.image_folder).glob("*.png"))

        for image_path in image_files:
            try:
                city_name = analyze_func(str(image_path))
                results[image_path.name] = city_name
            except Exception as e:
                logger.error(f"Error analyzing {image_path.name}: {str(e)}")
                results[image_path.name] = "ERROR"

        return results

    @staticmethod
    def find_most_common_city(
        results: Dict[str, str]
    ) -> Tuple[str, List[str], List[str]]:
        """Analyze results to find the most common city and outliers"""
        city_counts = Counter(results.values())
        most_common_city = city_counts.most_common(1)[0][0]

        matching_images = [
            img for img, city in results.items() if city == most_common_city
        ]
        outlier_images = [
            img for img, city in results.items() if city != most_common_city
        ]

        return most_common_city, matching_images, outlier_images

    def analyze_with_both_models(self) -> Tuple[str, str]:
        """Analyze images with both models and return most common cities"""
        anthropic_results = self.analyze_all_images("anthropic")
        openai_results = self.analyze_all_images("openai")

        anthropic_most_common_city, _, _ = self.find_most_common_city(anthropic_results)
        openai_most_common_city, _, _ = self.find_most_common_city(openai_results)

        return anthropic_most_common_city, openai_most_common_city
