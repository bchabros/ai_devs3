import os
import re
import asyncio
import base64
import requests
import anthropic
from typing import List, Optional, Tuple
import httpx
from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger
from langsmith import traceable
from pydantic import BaseModel
from src.prompt.s04e01 import TOOLS_PROMPT, DESCRIPTION_PROMPT
from src.send_task import send

load_dotenv()
# Configuration
class Config:
    CENTRALA_URL = os.getenv('CENTRALA_URL', '')
    API_KEY = os.getenv('API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    REQUIRED_ENV_VARS = ["LANGCHAIN_API_KEY", "ANTHROPIC_API_KEY"]

    @classmethod
    def validate(cls):
        """Validate all required environment variables are set."""
        missing_vars = [var for var in cls.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# API Models
class ApiRequest(BaseModel):
    task: str = "photos"
    apikey: str = Config.API_KEY
    answer: str


class ApiResponse(BaseModel):
    code: int
    message: str


class AsyncImageAnalyzer:
    """Async version of ImageAnalyzer for concurrent image processing."""

    def __init__(self):
        """Initialize the AsyncImageAnalyzer with Anthropic client."""
        logger.info("Initializing AsyncImageAnalyzer")
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.anthropic = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.client = httpx.AsyncClient()

    # The URL validation method in AsyncImageAnalyzer should also be updated:
    async def _check_image_availability(self, url: str) -> bool:
        """Async version of image availability check with URL cleanup."""
        try:
            logger.debug(f"Checking image availability at URL: {url}")

            # Clean up URL if it's doubled
            if url.count("https://") > 1:
                url = url[url.rindex("https://"):]
                logger.debug(f"Cleaned up doubled URL to: {url}")

            response = await self.client.head(url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image'):
                raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")

            logger.info(f"Image found - Type: {content_type}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to access image URL: {str(e)}")
            raise

    async def _url_to_base64(self, url: str) -> str:
        """Async version of URL to base64 conversion."""
        try:
            logger.debug(f"Converting image to base64: {url}")
            response = await self.client.get(url)
            response.raise_for_status()

            base64_data = base64.b64encode(response.content).decode('utf-8')
            logger.info("Successfully converted image to base64")
            return base64_data

        except Exception as e:
            logger.error(f"Failed to convert image to base64: {str(e)}")
            raise

    @staticmethod
    def _extract_analysis_details(response_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract action and reason from Claude's response."""
        action = None
        reason = None

        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('ACTION:'):
                action = line.split('ACTION:')[1].strip()
            elif line.startswith('REASON:'):
                reason = line.split('REASON:')[1].strip()

        return action, reason

    @traceable(run_type="tool")
    async def analyze_image(self, url: str) -> Optional[str]:
        """Async version of image analysis."""
        try:
            logger.info(f"Starting image analysis for URL: {url}")

            # Validate image
            await self._check_image_availability(url)
            base64_image = await self._url_to_base64(url)

            # Get Claude's analysis
            logger.debug("Preparing Claude prompt for image analysis")
            message = self.anthropic.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": TOOLS_PROMPT
                        }
                    ]
                }]
            )

            action, reason = self._extract_analysis_details(message.content[0].text)
            if action:
                logger.success(f"Recommended action: {action} for {url}")
            if reason:
                logger.success(f"Analysis reason: {reason}")

            return action

        except Exception as e:
            logger.error(f"Error in analyze_image: {str(e)}", exc_info=True)
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def send_api_request(query: str) -> ApiResponse:
    """Async version of API request sender."""
    async with httpx.AsyncClient() as client:
        data = ApiRequest(answer=query)
        response = await client.post(f"{Config.CENTRALA_URL}report", json=data.model_dump())
        return ApiResponse(**response.json())

async def extract_filename_from_response(response_message: str) -> str:
    """
    Extract filename from API response message, handling both full URLs and simple filenames.

    Args:
        response_message: The response message from the API

    Returns:
        str: The extracted filename

    Raises:
        ValueError: If no valid filename could be extracted
    """
    try:
        # Split the message into words and get the last part
        last_part = response_message.split()[-1]

        # If it's a full URL, extract just the filename
        if last_part.startswith('http'):
            filename = last_part.split('/')[-1]
        else:
            filename = last_part

        # Validate the extracted filename
        if not filename.endswith('.PNG'):
            raise ValueError(f"Invalid filename format: {filename}")

        return filename

    except Exception as e:
        logger.error(f"Failed to extract filename from response: {response_message}")
        raise ValueError(f"Could not extract valid filename from response: {str(e)}")


async def process_single_image(analyzer: AsyncImageAnalyzer, base_url: str, filename: str) -> str:
    """Process a single image until done."""
    try:
        current_filename = filename

        while True:
            # Ensure we're using the correct URL format
            current_url = f"{base_url}{current_filename}"
            if current_url.startswith(f"{base_url}{base_url}"):
                # Fix doubled base URL if it occurs
                current_url = current_url.replace(f"{base_url}{base_url}", base_url)

            logger.info(f"Processing image: {current_url}")

            result = await analyzer.analyze_image(current_url)

            if result == "DONE":
                logger.info(f"Processing complete for {current_filename}")
                return current_filename

            response = await send_api_request(f"{result} {current_filename}")
            logger.info(f"API Response for {current_filename}: {response.message}")

            try:
                new_filename = await extract_filename_from_response(response.message)
                current_filename = new_filename
                logger.debug(f"Extracted new filename: {current_filename}")
            except ValueError as e:
                logger.error(f"Error extracting filename: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        raise


async def process_multiple_images(base_url: str, filenames: List[str]) -> List[str] | List[BaseException]:
    """Process multiple images concurrently."""
    analyzer = AsyncImageAnalyzer()
    try:
        tasks = [process_single_image(analyzer, base_url, filename) for filename in filenames]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from the tasks
        final_results = []
        for filename, result in zip(filenames, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process {filename}: {str(result)}")
            else:
                final_results.append(result)

        return final_results
    finally:
        await analyzer.close()



class ImagePipeline:
    def __init__(self):
        load_dotenv()
        self.base_url = f"{os.getenv('CENTRALA_URL')}dane/barbara/"
        self.anthropic_client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _construct_image_urls(self, filenames: List[str]) -> List[str]:
        """Convert filenames to full URLs."""
        return [f"{self.base_url}{filename}" for filename in filenames]

    async def process_initial_images(self, initial_filenames: List[str]) -> List[str]:
        """First stage: Process initial images using the first script's logic."""
        logger.info("Starting initial image processing...")
        try:
            processed_filenames = await process_multiple_images(self.base_url, initial_filenames)
            logger.info(f"Initial processing complete. Results: {processed_filenames}")
            return processed_filenames
        except Exception as e:
            logger.error(f"Error in initial processing: {str(e)}")
            raise

    def analyze_processed_images(self, processed_filenames: List[str]) -> str:
        """Second stage: Analyze the processed images using the second script's logic."""
        logger.info("Starting final image analysis...")
        try:
            # Construct full URLs for the processed files
            image_urls = self._construct_image_urls(processed_filenames)

            # Create content list for all images
            content = []
            for idx, image_url in enumerate(image_urls, 1):
                # Add label text
                content.append({
                    "type": "text",
                    "text": f"\nPhoto {idx}:"
                })

                # Encode and add image
                response = requests.get(image_url)
                response.raise_for_status()
                base64_image = base64.b64encode(response.content).decode('utf-8')
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image
                    }
                })

            # Add the description prompt
            content.append({
                "type": "text",
                "text": DESCRIPTION_PROMPT
            })

            # Get analysis from Claude
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Error in final analysis: {str(e)}")
            raise

    @staticmethod
    def send_final_report(analysis: str) -> dict:
        """Send the final analysis to the API."""
        logger.info("Sending final report...")
        try:
            api_key = os.getenv('API_KEY')
            url = f"{os.getenv('CENTRALA_URL')}report"
            response = send(url, answer=analysis, apikey=api_key, task="photos")
            logger.info("Final report sent successfully")
            return response
        except Exception as e:
            logger.error(f"Error sending final report: {str(e)}")
            raise

    async def run_pipeline(self, initial_filenames: List[str]):
        """Run the complete pipeline."""
        try:
            # Stage 1: Process initial images
            processed_filenames = await self.process_initial_images(initial_filenames)

            # Stage 2: Analyze processed images
            analysis = self.analyze_processed_images(processed_filenames)

            # Stage 3: Send final report
            final_response = self.send_final_report(analysis)

            return final_response

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            raise

def send_request(query: str):
    data = ApiRequest(answer=query)
    response = httpx.post(f"{Config.CENTRALA_URL}report", json=data.model_dump())
    return ApiResponse(**response.json())


def extract_filenames(response_message: str) -> List[str]:
    """
    Extract filenames from API response message.
    Args:
        response_message: String containing the response message
    Returns:
        List of filenames found in the message
    """
    # Find all file patterns matching IMG_XXX.PNG
    pattern = r'IMG_\d+\.PNG'
    files = re.findall(pattern, response_message)

    # Remove duplicates while preserving order
    unique_files = list(dict.fromkeys(files))

    return unique_files