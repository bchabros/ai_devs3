import httpx
from pydantic import BaseModel
from typing import List, Any, Dict


class TaskRequest(BaseModel):
    task: str
    apikey: str
    answer: str | List[Any] | Dict


class QueryRequest(BaseModel):
    task: str
    apikey: str
    query: str | List[Any] | Dict


def send(
    url: str,
    task: str,
    apikey: str,
    answer: str | List[Any] | Dict,
    class_type: str = "send",
):
    """Send task solution for verification.

    Args:
        url (str): Verification URL
        task (str): Task ID (typically UPPERCASE)
        apikey (str): AI_DEVS_3API key
        answer (str | List[Any]): Task solution
        class_type: BaseModel pydantic class
    """
    if class_type == "query":
        payload = QueryRequest(task=task, apikey=apikey, query=answer)
    else:
        payload = TaskRequest(task=task, apikey=apikey, answer=answer)

    res = httpx.post(url, json=payload.model_dump())
    if res.status_code != 200:
        raise Exception(f"Failed to send data: {res.text}")
    return res.json()
