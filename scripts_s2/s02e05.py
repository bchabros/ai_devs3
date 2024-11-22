import os
import requests
from dotenv import load_dotenv
from loguru import logger

from src.prompt.s02e05 import SYSTEM_TEMPLATE_VISION, SYSTEM_TEMPLATE_CHAT
from src.s_02.e_05 import (
    aidevs_send_answer,
    group_files_by_type,
    openai_create,
    openai_vision_create,
    replace_placeholders_in_text,
    transfer_webpage_to_markdown,
    whisper_transcribe,
)


def run():
    url_article: str = f"{os.getenv('CENTRALA_URL')}dane/arxiv-draft.html"
    url_questions: str = (
        f"{os.getenv('CENTRALA_URL')}data/{os.getenv('API_KEY')}/arxiv.txt"
    )
    output_directory: str = "S02E05"
    markdown_name: str = "S02E05_webpage"
    system_template_vision = SYSTEM_TEMPLATE_VISION
    system_template_chat = SYSTEM_TEMPLATE_CHAT

    transfer_webpage_to_markdown(url_article, output_directory, markdown_name)

    grouped_files = group_files_by_type(output_directory)
    image_descriptions = dict()
    for image_name in grouped_files["Images"]:
        image = open(os.path.join(output_directory, image_name), "rb")
        response = openai_vision_create(
            system_template_vision, "", [image], model="gpt-4o-mini", temperature=0.1
        )
        logger.debug(f"IMAGE DESCRIPTION: {image_name}\n{response.content}")
        image_descriptions[image_name] = response.content
    audio_transcriptions = dict()
    for audio_name in grouped_files["Audio"]:
        transcription = whisper_transcribe(os.path.join(output_directory, audio_name))
        logger.debug(f"AUDIO TRANSCRIPTION: {audio_name}\n{transcription}")
        audio_transcriptions[audio_name] = transcription

    markdown_path = os.path.join(output_directory, markdown_name)
    with open(markdown_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()
    logger.debug("Successfully opened markdown content")

    webpage_complete_data = replace_placeholders_in_text(
        markdown_content, image_descriptions, audio_transcriptions
    )
    logger.debug("Webpage_complete_data is completed")

    questions_response = requests.get(url_questions)
    questions = questions_response.text
    logger.debug(f"QUESTIONS: {questions}")

    questions_dict = {}
    lines = questions.strip().split("\n")
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)  # Split only at the first '='
            questions_dict[key.strip()] = value.strip()

    answers = {}
    for question_id, question_content in questions_dict.items():
        response = openai_create(
            f"{webpage_complete_data}\n{system_template_chat}", question_content
        )
        answer = response.content
        logger.debug(f"QUESTION: {question_content}\nANSWER: {answer}")
        answers[question_id] = answer
    logger.debug(f"FINAL ANSWERS: {answers}")

    response_task = aidevs_send_answer(task="arxiv", answer=answers)
    if response_task.status_code == 200:
        logger.success(f"Request successful! Response:, {response_task.content}")
    else:
        logger.warning(
            f"Request failed with status code: {response_task.status_code}"
            f"Response content: {response_task.content}"
        )


if __name__ == "__main__":
    load_dotenv()
    run()
