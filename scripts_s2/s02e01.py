import os

from dotenv import load_dotenv

from src.s_02.e_01 import transcribe_audio_files, query_claude_with_json_context
from src.poligon import send

if __name__ == "__main__":

    load_dotenv()

    input_direction = "/Users/Chabi/Desktop/ai_devs/przesluchania/"
    output_direction = "/Users/Chabi/Desktop/ai_devs/przesluchania_output/"

    # convert .m4a file into transcript from folder
    transcribe_audio_files(
        os.environ["OPENAI_API_KEY"], input_direction, output_direction
    )

    # answer on context from transcript
    question = "Na jakiej ulicy znajduje się uczelnia, na której wykłada Andrzej Maj. Podaj nazwę tylko tej ulicy."
    output = query_claude_with_json_context(
        output_direction + "transcription.json", question=question
    )

    # send result
    endpoint = f"{os.environ.get('CENTRALA_URL')}report"
    res = send(endpoint, task="mp3", apikey=os.environ["API_KEY"], answer=output)
    print(res)
