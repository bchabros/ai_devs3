import os
import re
import anthropic
from typing import List, Dict
from loguru import logger

from src.send_task import send
from src.prompt.s03e03 import INITIAL_PROMPT


def get_claude_response(messages: List[Dict[str, str]]) -> Dict:
    client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Extract system message
    system_message = next(
        (msg["content"] for msg in messages if msg["role"] == "system"), ""
    )

    # Filter out system message from messages
    chat_messages = [msg for msg in messages if msg["role"] != "system"]

    response = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=1024,
        system=system_message,
        messages=chat_messages,
    )

    content = response.content[0].text

    query_match = re.search(r"QUERY:\s*(.+?)(?=REASONING:|$)", content, re.DOTALL)
    reasoning_match = re.search(
        r"REASONING:\s*(.+?)(?=IS_FINAL:|$)", content, re.DOTALL
    )
    is_final_match = re.search(r"IS_FINAL:\s*(true|false)", content, re.IGNORECASE)

    return {
        "query": query_match.group(1).strip() if query_match else None,
        "reasoning": reasoning_match.group(1).strip() if reasoning_match else None,
        "is_final": (
            is_final_match.group(1).lower() == "true" if is_final_match else False
        ),
    }


def create_sql_agent():
    messages = [
        {
            "role": "system",
            "content": "You are an expert SQL programmer. Format your responses with sections: QUERY, REASONING, IS_FINAL",
        },
        {
            "role": "user",
            "content": INITIAL_PROMPT,
        },
    ]

    while True:
        # Get next action from Claude
        response = get_claude_response(messages)
        logger.info(f"Claude's reasoning: {response['reasoning']}")
        logger.info(f"Executing query: {response['query']}")
        logger.info(f"Is final: {response['is_final']}")

        # Execute SQL query
        query_result = send(
            url="https://centrala.ag3nts.org/apidb",
            apikey=os.getenv("API_KEY"),
            answer=response["query"],
            task="database",
            class_type="query",
        )

        # Add interaction to context
        messages.extend(
            [
                {
                    "role": "assistant",
                    "content": f"QUERY: {response['query']}\nREASONING: {response['reasoning']}\nIS_FINAL: {response['is_final']}",
                },
                {
                    "role": "user",
                    "content": f"Query result: {query_result['reply']}\nWhat's your next step?",
                },
            ]
        )

        if response["is_final"]:
            return query_result["reply"]
