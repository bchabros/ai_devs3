import os
from anthropic import Anthropic


async def extract_question(page_content: str) -> str:
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
    Parse this website content and extract a question.
    There is only one question in the content.
    The question should be a single sentence.
    If there is no question, return an empty string

    Content:
    {page_content}
    """

    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


async def answer_question(question: str) -> str:
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
    Answer the question. The answer is a single integer number.
    Provide the answer only, without any other text, numbers, or characters.
    If you cannot answer the question, return 0.
    Question: {question}
    """

    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
