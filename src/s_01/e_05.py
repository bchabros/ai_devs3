import os
from enum import Enum
from typing import Optional

import requests
import logging
from dotenv import load_dotenv
from anthropic import Anthropic


class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class CensoredData:
    def __init__(
        self,
        provider: ModelProvider,
        anthropic_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost: 1143",
    ):
        """
        Initialize CensoredData with either Anthropic or Ollama configuration.

        Args:
            provider (ModelProvider): Which provider to use (ANTHROPIC or OLLAMA)
            anthropic_api_key (Optional[str]): Anthropic API key, required if provider is ANTHROPIC
            ollama_base_url (str): Base URL for Ollama API, used if provider is OLLAMA
        """
        self.provider = provider
        self.ollama_base_url = ollama_base_url
        self.client = None

        if provider == ModelProvider.ANTHROPIC:
            if not anthropic_api_key:
                raise ValueError("Missing ANTHROPIC_API_KEY environment variable")
            self.client = Anthropic(api_key=anthropic_api_key)
        self.logger = self.setup_logging()
        self.context_template = """
<objective>
Replace all presonal information (name + surname, city, street name + number and age) with the word: "CENZURA in the 
provided text.
</objective>

<rules>
- In the results we don't want to TWO words "CENZURA" next to each other.
- For name and surname change for one word "CENZURA".
- For street and number change for one word "CENZURA".
- For city change for one word "CENZURA".
- For age change for one word "CENZURA" age ussualy is before word "lat"
- Keep other words unchanged. 
- Do not change punctuation.
</rules>

<example>
<input>
Podejrzany: Krzysztof Kwiatkowski. Mieszka w Szczecinie przy ul. Różanej 12. Ma 31 lat.
</input>

<output>
Podejrzany: CENZURA. Mieszka w CENZURA przy ul. CENZURA. Ma CENZURA lat.
</output>
</example>

Here's the text: {text}
"""

    @staticmethod
    def setup_logging() -> logging.Logger:
        """
        Configure and return a logger instance.

        Returns:
            logging.Logger: Configured logger instance
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("censorship.log"), logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def download_text(self, url: str) -> str:
        """
        Download text from given URL.

        Args:
            url (str): URL to download text from

        Returns:
            str: Downloaded text content

        Raises:
            requests.RequestException: If download fails
        """
        self.logger.info(f"Attempting to download text from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        text = response.text
        self.logger.info(f"Successfully downloaded text: {text}")
        return text

    def censor_text_anthropic(
        self, text: str, model: str = "claude-3-haiku-20240307"
    ) -> str:
        """
        Use Claude to censor personal information in text.

        Args:
            text (str): Text to censor
            model (str, optional): Claude model to use. Defaults to "claude-3-haiku-20240307"

        Returns:
            str: Censored text
        """
        self.logger.info("Starting Anthropic text censorship process")
        context = self.context_template.format(text=text)
        message = self.client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": context}],
        )
        censored_text = message.content[0].text
        return censored_text

    def censor_text_ollama(self, text: str, model: str = "") -> str:
        """
        Use Ollama to censor personal information in text.

        Args:
            text (str): Text to censor
            model (str, optional): Ollama model to use

        Returns:
            str: Censored text
        """
        self.logger.info("Starting Ollama text censorship process")
        context = self.context_template.format(text=text)

        response = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json={"model": model, "prompt": context, "stream": False},
        )
        response.raise_for_status()

        result = response.json()
        return result["response"]

    def censor_text(self, text: str, model: Optional[str] = None) -> str:
        """
        Censor personal information in text using the configured provider.

        Args:
            text (str): Text to censor
            model (Optional[str]): Model to use. If None, uses default for provider

        Returns:
            str: Censored text
        """
        self.logger.info(
            f"Starting text censorship process using {self.provider.value}"
        )

        if self.provider == ModelProvider.ANTHROPIC:
            model = model or "claude-3-haiku-20240307"
            censored_text = self.censor_text_anthropic(text, model)
        else:  # OLLAMA
            model = model or "mistral"
            censored_text = self.censor_text_ollama(text, model)

        self.logger.info(f"Text successfully censored: {censored_text}")
        return censored_text

    @classmethod
    def from_env(cls) -> "CensoredData":
        """
        Create CensoredData instance using environment variables.

        Environment variables:
        - PROVIDER: 'anthropic' or 'ollama'
        - ANTHROPIC_API_KEY: Required if provider is 'anthropic'
        - OLLAMA_BASE_URL: Optional, defaults to http://localhost:11434

        Returns:
            CensoredData: Initialized instance

        Raises:
            ValueError: If required environment variables are missing
        """
        load_dotenv()

        provider_str = os.environ.get("PROVIDER", "ollama").lower()
        if provider_str not in ["anthropic", "ollama"]:
            raise ValueError("PROVIDER must be either 'anthropic' or 'ollama'")

        provider = ModelProvider(provider_str)

        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        if provider == ModelProvider.ANTHROPIC and not anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when using Anthropic provider"
            )

        return cls(
            provider=provider,
            anthropic_api_key=anthropic_api_key,
            ollama_base_url=ollama_base_url,
        )

    def process_text(self, input_url: str, model: Optional[str] = None) -> str:
        """
        Complete process of downloading and censoring text.

        Args:
            input_url (str): URL to download text from
            model (Optional[str]): Model to use. If None, uses default for provider

        Returns:
            str: Censored text
        """
        try:
            original_text = self.download_text(input_url)
            return self.censor_text(original_text, model)
        except Exception as e:
            self.logger.error(f"Error processing text: {str(e)}", exc_info=True)
            raise