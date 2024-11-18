import httpx
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

def get_questions():
    load_dotenv()
    url = os.getenv("CENTRALA_URL") + "data/" + os.getenv("API_KEY") + "/arxiv.txt"
    r = httpx.get(url)
    return r.text.split("\n")


def trim_questions(questions) -> dict:
    trimmed = dict()
    for question in questions:
        if len(question.split("=")) == 2:
            trimmed.update({question.split("=")[0]: question.split("=")[1]})
    return trimmed

def get_document():
    load_dotenv()
    url = os.getenv("CENTRALA_URL") + "dane/arxiv-draft.html"
    r = httpx.get(url)
    return r.text


html_document = get_document()
questions = trim_questions(get_questions())

print(questions)


def extract_content_objects(document: str):
    load_dotenv()
    system_prompt = """

    You are a HTML document parser.
    Your task is to extract content objects from the document while taking into account the context of each object.


    1. There are 3 types of content objects:
    a. Text
    - HTML block starting with a heading.
    - The heading can be recognized on the basis of font size and formatting - it's typically visibly larger than the paragraph body.
    b. Audio clip - a HTML link to an mp3 file.
    c. Image
    - a HTML element (often figure or img) with the src attribute pointing to an image url
    - usually accompanied by a figcaption element with a caption
    2. Find all content objects in the document and assign them numeric IDs and correct types.
    3. Associate each content object with context.
    - Context is a list of IDs of other content objects that are related to this object.
    - Two content objects are related if they are in proximity to each other in the document - text next to image, text next to audio, text next to text and so on.
    - Two objects are related if they are within 1-2 objects of each other in the document sequence.
    4. Create content objects for all identified elements and return them in format described in the OUTPUT section.

    Important - the image might be place in the middle of text block. In such case, the text block shoud NOT be divided into two separate content objects.
    Example of such case:
    Heading
    Text before image
     # image block
    More text
    Subheading
    In this case the text block spans from H1 to H2 and should be treated as one content object and the image should be treated as separate content object.



    Output must be a valid JSON object with the following structure:
    {
    "content_objects": [
        {
        "id": ,
        "type": <"text" | "audio" | "image">,
        "context": [],
        "content": ,
        "caption":  (only for image type) or null
        }
    ]
    }

    Each content object should represent one of the identified document elements.

    Examples:
    {
    "content_objects": [
        {
        "id": 1,
        "type": "text",
        "context": [2, 3],
        "content": "This is a text content object.",
        "caption": null
        },
        {
        "id": 2,
        "type": "audio",
        "context": [1],
        "content": "https://example.com/audio.mp3",
        "caption": null
        },
        {
        "id": 3,
        "type": "image",
        "context": [1],
        "content": "https://example.com/image.jpg",
        "caption": "This is a caption for the image taken from figcaption."
        }
    ]
    }
    IMPORTANT RULES:
    - Ensure the output is a valid JSON object.
    - Use double quotes for all strings.
    - Make sure the JSON is parsable without any syntax errors.
    - Don't wrap the JSON into any other data structure or any markup. Yo must return only the JSON object.

    """

    ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": document},
        ],
    )

    content = response.choices[0].message.content
    content = content.lstrip("```json\n").rstrip("\n```")
    return json.loads(content)["content_objects"]


data = extract_content_objects(html_document)
print(data)

def data_preprocessing(data):
    for item in data:
        if item["type"] == "image":
            if not item["content"].startswith("http"):
                item["content"] = f"{os.getenv('CENTRALA_URL')}dane/{item['content']}"
        if item["type"] == "audio":
            if not item["content"].startswith("http"):
                item["content"] = f"{os.getenv('CENTRALA_URL')}dane/{item['content']}"
    return data

processed_data = data_preprocessing(data)


for d in processed_data:
    if d["type"] == "image":
        print(d)

for d in processed_data:
    if d["type"] == "audio":
        print(d)

for d in processed_data:
    if d["type"] == "text":
        print(d)


def describe_image(image_url, image_caption):
    load_dotenv()
    system_prompt = """

    You are an image description generator. Your task is to generate a description for the image provided in the input taking also into account the provided caption.


    - Focus on objects, landmarks, features.
    - Don't describe atmosphere or mood.
    - Use concise language.
    - Analyze the caption and the image to generate a coherent description - the caption shouldn't contradict the image.
    - The description should be 1-3 sentences long.
    - The description should incorporate the information from caption.

    """

    ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                },
                {
                    "type": "text",
                    "text": f"Describe the image. The caption is {image_caption}."
                }
            ]},
        ],
    )

    return response.choices[0].message.content

annotated_images = []

for item in processed_data:
    if item["type"] == "image":
        description = describe_image(item["content"], image_caption=item["caption"])
        annotated_images.append({"id": item["id"], "description": description})

import io


def transcribe_audio(audio_url):
    load_dotenv()

    ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    audio = httpx.get(audio_url)

    buf = io.BytesIO(audio.content)
    buf.name = "file.mp3"

    transcription = ai.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
    )

    return transcription.text


transcribed_audio = []

for item in processed_data:
    if item["type"] == "audio":
        transcription = transcribe_audio(item["content"])
        transcribed_audio.append({"id": item["id"], "transcription": transcription})



import pickle

with open("annotated_images.pkl", "wb") as f:
    pickle.dump(annotated_images, f)

with open("transcribed_audio.pkl", "wb") as f:
    pickle.dump(transcribed_audio, f)

with open("processed_data.pkl", "wb") as f:
    pickle.dump(processed_data, f)

_data = processed_data.copy()

for item in _data:
    if item["type"] == "text": pass
    if item["type"] == "image":
        for image in annotated_images:
            if item["id"] == image["id"]:
                item["content"] = image["description"]
    if item["type"] == "audio":
        for audio in transcribed_audio:
            if item["id"] == audio["id"]:
                item["content"] = audio["transcription"]

with open("final_data.pkl", "wb") as f:
    pickle.dump(_data, f)

SYS_PROMPT = f"""

    You are a question answering model. Your task is to answer the question based on the provided information.


    - The information is a collection of various objects.
    - Each object has an ID, type, context pointers, and content.
    - Each object can represent a text block, an image, or an audio clip. This is stated by the "type" field.
    - The "content" field contains the actual content of the object. In case of images and audio clips, the content is a description or transcription.
    - The "context" field is a list of IDs of other objects that are closely related to this object.
    - Follow these relationships to analyze how data is interrelated but also take into account other objects in entire data.
    - To answer the question, consider not only the content of the object but also its related objects as indicated by the "context" field.
    - Explore the "context" field recursively to gather all relevant information, but prioritize direct relationships over distant ones.
    - Focus on objects that directly contribute to answering the question, avoiding irrelevant details.
    - For "image" objects, use the provided description or caption to infer information but also take into account the context pointers which may give important tips.
    - For "audio" objects, use the transcription or description to extract relevant data.
    - If conflicting information is found, prioritize the most directly related object in the context.
    - If no relevant information exists, state this explicitly in the answer.
    - Include names of objects, descriptions, and other relevant details in the answer.
    - When searching for an acronym's explanation, consider not only the immediate context of objects but also recursively explore related objects.
    - Use direct relationships first, and only if no explanation is found, explore more distant relationships.
    - Always expand all acronyms and abbreviations using all informatation provided - make sure that you focus on finding the proper solution.

    Answer the question based on entire provided information.


    Your answer must be a single sentence.
    Be accurate based on the provided context.
    If no relevant information is found, respond with "The information is not available in the provided context."


    IMPORTANT: all answers must be in Polish.
    IMPORTANT: look carefully at all provided data objects before answering the question.
"""

SYS_PROMPT_2 = f"""

    You are a question answering model. Your task is to answer the question based on the provided information.


    - The information is a collection of various objects.
    - Each object has an ID, type, context pointers, and content.
    - Each object can represent a text block, an image, or an audio clip. This is stated by the "type" field.
    - The "content" field contains the actual content of the object. In case of images and audio clips, the content is a description or transcription.
    - Focus on objects that directly contribute to answering the question, avoiding irrelevant details.
    - For "image" objects, use the provided description or caption to infer information but also take into account the context pointers which may give important tips.
    - For "audio" objects, use the transcription or description to extract relevant data.
    - If conflicting information is found, prioritize the most directly related object in the context.
    - If no relevant information exists, state this explicitly in the answer.
    - Include names of objects, descriptions, and other relevant details in the answer.
    - When searching for an acronym's explanation, consider not only the immediate context of objects but also recursively explore related objects.
    - Use direct relationships first, and only if no explanation is found, explore more distant relationships.
    - Always expand all acronyms and abbreviations using all informatation provided - make sure that you focus on finding the proper solution.

    Answer the question based on entire provided information.


    Your answer must be a single sentence.
    Be accurate based on the provided context.
    If no relevant information is found, respond with "The information is not available in the provided context."


    IMPORTANT: all answers must be in Polish.
    IMPORTANT: look carefully at all provided data objects before answering the question.
"""

for d in _data:
    if d["type"] == "text":
        print(d["content"])


def answer_question(question: str, data: list[dict]):
    load_dotenv()
    prompt = SYS_PROMPT

    ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"This is the question: {question}"},
            {"role": "user", "content": f"This is the data: {data}"},
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


question = "Od czego pochodzą litery BNW w nazwie nowego modelu językowego?"

answer = answer_question(question, _data)
print(answer)

print(questions)

answers = []
for i, q in questions.items():
    answers.append((i, answer_question(q, _data)))
print(answers)


result = {
    question_id: answer for question_id, answer in answers
}
print(result)
from dotenv import load_dotenv

from src.poligon import send
import os
load_dotenv()

result = {'01': 'Podczas pierwszej próby transmisji materii w czasie użyto truskawki.', '02': 'Testowa fotografia użyta podczas testu przesyłania multimediów została wykonana na rynku w Krakowie.', '03': 'Bomba chciał znaleźć hotel w Grudziądzu.', '04': 'Resztki dania pozostawione przez Rafała to kawałki pizzy hawajskiej z ananasem, znalezione w pobliżu komory temporalnej.', '05': 'Litery BNW w nazwie nowego modelu językowego BNW-01 pochodzą od „Brave New World” – Nowy Wspaniały Świat.'}


url = os.environ.get("CENTRALA_URL") + "report"
task = "arxiv"
api_key = os.environ.get("API_KEY")
res = send(url, task, api_key, result)
print(res)