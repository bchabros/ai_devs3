import json
import os

import anthropic

import openai
from pathlib import Path
import logging

from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
)  # Define the log message format
logger = logging.getLogger("simpler_logger")


def transcribe_audio_files(api_key, input_dir, output_dir) -> None:
    """
    Transcribe multiple .m4a files using OpenAI's Whisper API

    Parameters:
    api_key (str): OpenAI API key
    input_directory (str): Directory containing .m4a files
    output_directory (str): Directory to save transcription results
    """
    # Set up OpenAI client
    openai.api_key = api_key
    client = OpenAI()

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get all .m4a files in the input directory
    audio_files = list(Path(input_dir).glob("*.m4a"))

    # Dictionary to store all transcriptions
    all_transcriptions = {"transcriptions": []}

    for audio_path in audio_files:
        try:
            logger.info(f"Processing {audio_path.name}")

            with open(audio_path, "rb") as audio_file:
                # Send to OpenAI for transaction
                transcipt = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )

            # Add transcription to the collection
            transcription_entry = {
                "file_name": audio_path.name,
                "transcription": transcipt.text,
            }
            all_transcriptions["transcriptions"].append(transcription_entry)

            logger.info(f"Transcription completed for: {audio_path.name}")

        except Exception as e:
            logger.error(f"Error processing {audio_path.name}: {str(e)}")

        # Save transcription to a JSON file
        output_path = Path(output_dir) / "transcription.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_transcriptions, f, ensure_ascii=False, indent=2)

        logger.info(f"Transcription saved to: {output_path}")


def query_claude_with_json_context(json_path: str, question: str) -> str:
    """
    Read transcriptions from JSON file and query Claude with the context

    Parameters:
    json_path (str): Path to the JSON file with transcriptions
    question (str): Question to ask Claude
    """
    client = anthropic.Client(api_key=os.environ["ANTHROPIC_API_KEY"])

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Combine all transcriptions into one context
    context = "\n\n".join(
        f"File: {item['file_name']}\nContent: {item['transcription']}"
        for item in data["transcriptions"]
    )

    # Create the message for Claude
    system_prompt = """
       You are an assistant tasked with analyzing transcribed audio content and answering questions based on that content.
       You should focus specifically on finding information about locations, institutions, and people mentioned in the transcriptions.
       Please provide specific and precise answers, citing which file the information came from when possible.
       Remember that witness statements may be contradictory, some may be wrong, and others may answer in rather bizarre ways.
       The street name is not mentioned in the transcript. You must use the model's internal knowledge to get the answer.
       As an answer just give only street name.
       """

    user_message = f"""
       Here are the transcriptions of several audio files:

       {context}

       Based on the above context, please answer this question:
       {question}
       """

    # Query Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        system=system_prompt,
        max_tokens=1000,
        messages=[{"role": "user", "content": user_message}],
    )

    logger.info("Model response:")
    logger.info(message.content[0].text)
    return message.content[0].text
