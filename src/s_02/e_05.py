import httpx
import io
import pickle
import json
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from src.prompt.s02e05 import system_prompt_qa, system_prompt_image, system_prompt_parser


class DocumentProcessor:
    def __init__(self):
        self._setup_logging()
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.base_url = os.getenv("CENTRALA_URL")
        self.api_key = os.getenv("API_KEY")
        self.processed_data = None
        self.annotated_images = []
        self.transcribed_audio = []
        self.logger.info("DocumentProcessor initialized")

    def _setup_logging(self):
        self.logger = logging.getLogger('DocumentProcessor')
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # File handler
        file_handler = logging.FileHandler('document_processor.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def get_questions(self) -> dict:
        self.logger.info("Fetching questions")
        url = f"{self.base_url}data/{self.api_key}/arxiv.txt"
        try:
            response = httpx.get(url)
            response.raise_for_status()
            questions = response.text.split("\n")
            result = {q.split("=")[0]: q.split("=")[1] for q in questions if "=" in q}
            self.logger.debug(f"Retrieved {len(result)} questions")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching questions: {str(e)}")
            raise

    def get_document(self) -> str:
        self.logger.info("Fetching document")
        url = f"{self.base_url}dane/arxiv-draft.html"
        try:
            response = httpx.get(url)
            response.raise_for_status()
            self.logger.debug(f"Document retrieved, size: {len(response.text)} characters")
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching document: {str(e)}")
            raise

    def extract_content_objects(self, document: str) -> list:
        self.logger.info("Extracting content objects")
        system_prompt = system_prompt_parser
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": document},
                ],
            )
            content = response.choices[0].message.content
            self.logger.debug(f"Raw API response content: {content}")
            content = content.lstrip("```json\n").rstrip("\n```")
            parsed_content = json.loads(content)
            self.logger.debug(f"Extracted {len(parsed_content['content_objects'])} content objects")
            return parsed_content["content_objects"]
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            self.logger.error(f"Problematic content: {content}")
            raise
        except Exception as e:
            self.logger.error(f"Error extracting content objects: {str(e)}")
            raise

    def preprocess_data(self, data: list) -> list:
        self.logger.info("Preprocessing data")
        try:
            for item in data:
                if item["type"] in ["image", "audio"] and not item["content"].startswith("http"):
                    item["content"] = f"{self.base_url}dane/{item['content']}"
            self.logger.debug(f"Preprocessed {len(data)} items")
            return data
        except Exception as e:
            self.logger.error(f"Error preprocessing data: {str(e)}")
            raise

    def describe_image(self, image_url: str, image_caption: str) -> str:
        self.logger.info(f"Describing image: {image_url}")
        system_prompt = system_prompt_image
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": f"Describe the image. The caption is {image_caption}."}
                    ]},
                ],
            )
            description = response.choices[0].message.content
            self.logger.debug(f"Generated description: {description}")
            return description
        except Exception as e:
            self.logger.error(f"Error describing image: {str(e)}")
            raise

    def transcribe_audio(self, audio_url: str) -> str:
        self.logger.info(f"Transcribing audio: {audio_url}")
        try:
            audio = httpx.get(audio_url)
            buf = io.BytesIO(audio.content)
            buf.name = "file.mp3"
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=buf,
            )
            self.logger.debug(f"Generated transcription: {transcription.text}")
            return transcription.text
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise

    def process_document(self):
        self.logger.info("Starting document processing")
        try:
            document = self.get_document()
            data = self.extract_content_objects(document)
            self.processed_data = self.preprocess_data(data)

            for item in self.processed_data:
                if item["type"] == "image":
                    description = self.describe_image(item["content"], item["caption"])
                    self.annotated_images.append({"id": item["id"], "description": description})
                elif item["type"] == "audio":
                    transcription = self.transcribe_audio(item["content"])
                    self.transcribed_audio.append({"id": item["id"], "transcription": transcription})

            self.logger.info("Document processing completed")
        except Exception as e:
            self.logger.error(f"Error in process_document: {str(e)}")
            raise

    def save_results(self):
        self.logger.info("Saving results")
        try:
            with open("annotated_images.pkl", "wb") as f:
                pickle.dump(self.annotated_images, f)
            with open("transcribed_audio.pkl", "wb") as f:
                pickle.dump(self.transcribed_audio, f)
            with open("processed_data.pkl", "wb") as f:
                pickle.dump(self.processed_data, f)

            final_data = self.processed_data.copy()
            for item in final_data:
                if item["type"] == "image":
                    for image in self.annotated_images:
                        if item["id"] == image["id"]:
                            item["content"] = image["description"]
                elif item["type"] == "audio":
                    for audio in self.transcribed_audio:
                        if item["id"] == audio["id"]:
                            item["content"] = audio["transcription"]

            with open("final_data.pkl", "wb") as f:
                pickle.dump(final_data, f)
            self.logger.info("Results saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            raise

    def answer_question(self, question: str) -> str:
        self.logger.info(f"Answering question: {question}")
        system_prompt = system_prompt_qa
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"This is the question: {question}"},
                    {"role": "user", "content": f"This is the data: {self.processed_data}"},
                ],
                temperature=0.1
            )
            answer = response.choices[0].message.content
            self.logger.debug(f"Generated answer: {answer}")
            return answer
        except Exception as e:
            self.logger.error(f"Error answering question: {str(e)}")
            raise

    def process_questions(self) -> dict:
        self.logger.info("Processing questions")
        try:
            questions = self.get_questions()
            answers = [(q_id, self.answer_question(q)) for q_id, q in questions.items()]
            result = {question_id: answer for question_id, answer in answers}
            self.logger.debug(f"Processed {len(result)} questions")
            return result
        except Exception as e:
            self.logger.error(f"Error processing questions: {str(e)}")
            raise

    def send_results(self, result: dict):
        self.logger.info("Sending results")
        try:
            from src.poligon import send
            url = f"{self.base_url}report"
            task = "arxiv"
            response = send(url, task, self.api_key, result)
            self.logger.debug(f"Send results response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error sending results: {str(e)}")
            raise

    def run(self):
        self.logger.info("Starting document processor run")
        try:
            self.process_document()
            self.save_results()
            results = self.process_questions()
            self.logger.info(results)
            response = self.send_results(results)
            self.logger.info("Document processor run completed successfully")
            return response
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            raise
