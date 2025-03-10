import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List

import httpx
from openai import OpenAI


@dataclass
class Question:
    question: str
    answer: int | str


@dataclass
class DataRepairParser:
    """
    A data class for parsing and repairing data, especially focused on evaluating and fixing math questions.

    Attributes:
        origin_url (str): The origin URL from which data is fetched.
        cache_path (Optional[Path]): The optional path to a local cache file for data persistence.

    Methods:
        __post_init__: Initializes the object after the dataclass __init__ method.
        _setup_logging: Initializes the logging configuration for the DataRepair system.
        _load_data: Loads data either from a cache or a remote source.
        _load_from_cache: Loads data from a cache file and returns it as a dictionary.
        _load_data_from_remote: Fetches data from a remote URL and optionally caches it locally.
        repair: Repairs questions by evaluating if they are standard math problems or special cases, using an LLM model if necessary.
        _send_to_model: Sends a question to the LLM model for analysis and repair.
        prepare_for_verification: Prepares the repaired data for verification by converting it to a JSON string.
    """

    origin_url: str
    cache_path: Optional[Path] = Path("data.json")

    def __post_init__(self) -> None:
        """
        Initializes the object after the dataclass __init__ method.
        Sets up OpenAI client, logging, and loads data.

        :return: None
        """
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._setup_logging()
        self.data = self._load_data()
        self.questions = self.data["test-data"]

    def _setup_logging(self) -> None:
        """
        Initializes the logging configuration for the DataRepair system.

        The logging is set to INFO level and the format includes the timestamp,
        log level, and log message. A stream handler is used to output the logs
        to the console. An instance of the logger is also created and a message
        indicating the initialization of the DataRepair system is logged.

        :return: None
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing DataRepair system")

    def _load_data(self) -> Dict:
        """
        :return: A dictionary containing data loaded from either a cache or a remote source.
        """
        if self.cache_path and self.cache_path.exists():
            self.logger.info("Using cached data")
            return self._load_from_cache()
        return self._load_data_from_remote()

    def _load_from_cache(self) -> Dict:
        """
        Loads data from a cache file and returns it as a dictionary.

        :return: The data loaded from the cache file, parsed into a dictionary.
        """
        return json.loads(self.cache_path.read_text())

    def _load_data_from_remote(self) -> Dict:
        """
        Fetches data from a remote URL and optionally caches it locally.

        Retrieves JSON data from the specified origin URL and ensures the HTTP response
        is successful. If a cache path is provided, the data is written to a local file.

        :return: A dictionary containing the data fetched from the remote URL.
        """
        response = httpx.get(self.origin_url)
        response.raise_for_status()
        data = response.json()

        if self.cache_path:
            self.cache_path.write_text(json.dumps(data))

        return data

    def repair(self) -> List[Dict]:
        """
        :return: A list of repaired question dictionaries. Each dictionary contains a 'question'
                 and 'answer' key. The function evaluates whether each question is a standard
                 math problem or a special case, and repairs it if necessary using an LLM model.
        """
        repaired = []
        pattern = r'{"question":\s*"(\d+)\s*([+\-*/])\s*(\d+)",\s*"answer":\s*(\d+)}'
        for question in self.questions:
            # Is the question standard math or a special case?
            if not re.match(pattern, json.dumps(question)):
                # Special case always goes to LLM for repair
                self.logger.info(f"Special case: {question}")
                res = self._send_to_model(question)
                self.logger.info(f"Repaired special case: {res}")
                repaired.append(res)
            else:
                # Is the math question correct?
                q, a = question["question"], question["answer"]
                if eval(q) == a:
                    repaired.append(question)
                else:
                    # Repair the math question
                    self.logger.info(f"Found a broken math question: {question}")
                    res = self._send_to_model(question)
                    self.logger.info(f"Repaired broken math question: {res}")
                    repaired.append(res)

        return repaired

    def _send_to_model(self, question: Dict) -> str:
        """
        :param question: A dictionary representing the question and answer pair to be analyzed and possibly corrected.
        :return: A string representing the analyzed and corrected question-answer pair in JSON format.
        """
        system_prompt = """
        <objective>
        You are supposed to analyze pairs of questions and answers and provide correct answers or fix mistakes.
        Data will be provided as list of JSON formatted objects. Question is marked as "question" or "q" and answer is marked as "answer" or "a".
        Sometimes data can have nested structures, but you should always look for the "question" or "q" and "answer" and "a" keys.
        </objective>
        <rules>
        - If question is a math operation, set answer field to correct number.
        - If question is not a math operation, set answer field to correct string.
        - If answer is incorrect, provide the correct answer. 
        - If answer is correct just return the data as is.
        - You MUST ALWAYS return the data in the same format as it was provided.
        </rules>
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Repair this question: {json.dumps(question)}",
                    },
                ],
            )
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"Error in AI question analysis: {str(e)}")
            raise e

    def prepare_for_verification(self, data: List[Dict]) -> str:
        """
        :param data: A list of dictionaries containing test data to be prepared for verification.
        :return: A JSON string containing the API key, description, copyright information, and the provided test data.
        """
        return json.dumps(
            {
                "apikey": os.environ["API_KEY"],
                "description": self.data["description"],
                "copyright": self.data["copyright"],
                "test-data": data,
            }
        )
