import base64
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List

import aiofiles
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from langfuse.decorators import observe, langfuse_context

from src.prompt.s02e04 import prompt_text, prompt_image

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ContentClassifier:
    def __init__(self, claude_api_key: str, openai_api_key: str) -> None:
        self.logger = logging.getLogger(__name__)
        self.claude_client = AsyncAnthropic(api_key=claude_api_key)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.logger.info("ContentClassifier initialized")

    @observe(as_type="generation")
    async def classify_text(self, text: str, filename: str = "unknown") -> str:
        """
        Classifies the given text using a specified model and logs the processed information.

        Args:
            text: The text to be classified.
            filename: The name of the file associated with the text, default is "unknown".

        Returns:
            The classification result of the input text.
        """
        try:
            self.logger.debug(
                f"[{filename}] Processing text input of length: {len(text)}"
            )

            kwargs = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 300,
                "messages": [
                    {"role": "user", "content": prompt_text.format(text=text)}
                ],
            }

            langfuse_context.update_current_observation(
                input=kwargs["messages"],
                model=kwargs["model"],
                metadata={"filename": filename},
            )

            response = await self.claude_client.messages.create(**kwargs)

            langfuse_context.update_current_observation(
                usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                }
            )

            classification = response.content[0].text
            # self.logger.info(f"Text classified as: {classification}")
            self.logger.info(f"[{filename}] Classification result: {classification}")
            return classification
        except Exception as e:
            # self.logger.error(f"Error in classify_text: {str(e)}", exc_info=True)
            self.logger.error(
                f"[{filename}] Error in classify_text: {str(e)}", exc_info=True
            )
            raise

    async def process_text_file(self, filepath: str) -> str:
        """
        Process a text file asynchronously and classify its content.

        Args:
            filepath (str): The path to the text file to be processed.

        Returns:
            str: The classification result of the text file content.
        """
        try:
            filename = os.path.basename(filepath)
            self.logger.info(f"Processing text file: {filepath}")
            async with aiofiles.open(filepath, "r") as file:
                content = await file.read()
                return await self.classify_text(content, filename)
        except FileNotFoundError:
            self.logger.error(f"Text file not found: {filepath}")
            raise
        except Exception as e:
            self.logger.error(
                f"Error processing text file {filepath}: {str(e)}", exc_info=True
            )
            raise

    @observe()
    async def process_audio_file(self, filepath: str) -> str:
        """
        Processes an audio file to generate a transcription and classify the text.

        Args:
            filepath (str): Path to the audio file to be processed.

        Returns:
            str: The classification result of the transcribed text.

        Raises:
            Exception: If an error occurs during the processing of the audio file.
        """
        temp_dir = Path(filepath).parent / "temp_transcription"
        self.logger.info(f"Processing audio file: {filepath}")

        try:
            temp_dir.mkdir(exist_ok=True)
            self.logger.debug(f"Created temporary directory: {temp_dir}")

            self.logger.info("Starting audio transcription")
            transcript = await self.openai_client.audio.transcriptions.create(
                file=open(filepath, "rb"), model="whisper-1"
            )
            return await self.classify_text(transcript.text)

        except Exception as e:
            self.logger.error(
                f"Error processing audio file {filepath}: {str(e)}", exc_info=True
            )
            raise
        finally:
            if temp_dir.exists():
                import shutil

                self.logger.debug(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir)

    @observe(as_type="generation")
    async def process_image_file(self, filepath: str) -> str:
        """
        Processes an image file, sending it to a classification model via an API, and returns
        the classification result.

        Args:
            filepath (str): The file path of the image to be processed.

        Returns:
            str: The classification result of the image or "error" if an exception occurs.
        """
        try:
            self.logger.info(f"Processing image file: {filepath}")
            base64_image = self._encode_image(filepath)
            self.logger.debug("Image encoded to base64")

            kwargs = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_image},
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
                ],
            }

            langfuse_context.update_current_observation(
                input=kwargs["messages"],
                model=kwargs["model"],
                metadata={"filepath": filepath},
            )

            response = await self.claude_client.messages.create(**kwargs)

            langfuse_context.update_current_observation(
                usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                }
            )

            classification = response.content[0].text
            self.logger.info(f"Image classified as: {classification}")
            return classification

        except Exception as e:
            self.logger.error(
                f"Error analyzing image {filepath}: {str(e)}", exc_info=True
            )
            return "error"

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """
        Encodes an image to a base64 string.

        Args:
            image_path (str): Path to the image file to encode.

        Returns:
            str: The base64 encoded string of the image.

        Raises:
            Exception: If there is any issue in reading the image file or encoding it.
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logging.error(f"Error encoding image {image_path}: {str(e)}", exc_info=True)
            raise

    @observe()
    async def process_file(self, filepath: str) -> tuple[str, str]:
        """
        Processes files based on their extension and classifies them accordingly.

        Args:
            filepath (str): The path to the file that needs to be processed.

        Returns:
            tuple[str, str]: A tuple containing the file path and its
            classification. In case of an error, the classification will be
            "error".
        """
        _, ext = os.path.splitext(filepath)
        self.logger.info(f"Processing file: {filepath} with extension: {ext}")

        try:
            if ext == ".txt":
                classification = await self.process_text_file(filepath)
            elif ext == ".mp3":
                classification = await self.process_audio_file(filepath)
            elif ext == ".png":
                classification = await self.process_image_file(filepath)
            else:
                self.logger.error(f"Unsupported file extension: {ext}")
                raise ValueError(f"Unsupported file extension: {ext}")

            self.logger.info(f"File {filepath} classified as: {classification}")
            return filepath, classification
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {str(e)}", exc_info=True)
            return filepath, "error"

    @observe()
    async def classify_folder(self, folder_path: str) -> Dict[str, List[str]]:
        """
        Classifies files in the specified folder into categories based on their content.
        The files are classified asynchronously, and supported file types are .txt,
        .mp3, and .png.

        Args:
            folder_path (str): The path of the folder containing files to classify.

        Returns:
            Dict[str, List[str]]: A dictionary with keys "people" and "hardware". Each key
            maps to a list of filenames belonging to its category.

        """
        self.logger.info(f"Starting folder classification: {folder_path}")

        files = [
            f for f in os.listdir(folder_path) if f.endswith((".txt", ".mp3", ".png"))
        ]
        self.logger.info(f"Found {len(files)} files to process")

        tasks = [self.process_file(os.path.join(folder_path, f)) for f in files]
        results = await asyncio.gather(*tasks)

        classification = {"people": [], "hardware": []}

        for filepath, result in results:
            if result == "people":
                classification["people"].append(os.path.basename(filepath))
            elif result == "hardware":
                classification["hardware"].append(os.path.basename(filepath))

        self.logger.info(
            f"Classification complete. Found {len(classification['people'])} people files and {len(classification['hardware'])} hardware files"
        )
        return classification
