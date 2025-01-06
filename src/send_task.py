import httpx
from pydantic import BaseModel
from typing import List, Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import json


class TaskRequest(BaseModel):
    task: str
    apikey: str
    answer: str | List[Any] | Dict


class QueryRequest(BaseModel):
    task: str
    apikey: str
    query: str | List[Any] | Dict


class QueryRequestS05E04(BaseModel):
    task: str
    apikey: str
    answer: str | List[Any] | Dict
    justUpdate: bool = False


class S03E03Request(BaseModel):
    apikey: str
    query: str


class QueryResponse(BaseModel):
    reply: Any
    error: str


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

def send_s03e04(
    url: str,
    apikey: str,
    query: str,
):
    """Send task to get info .

    Args:
        url (str): Verification URL
        apikey (str): AI_DEVS_3API key
        query (str): Query to url
    """
    payload = S03E03Request(apikey=apikey, query=query)

    res = httpx.post(url, json=payload.model_dump())
    if res.status_code != 200:
        raise Exception(f"Failed to send data: {res.text}")
    return res.json()


def send_query(url: str, query: str, apikey: str):
    """Send prompt to Database"""
    data = QueryRequest(query=query,
                        task="database",
                        apikey=apikey)
    res = httpx.post(url, data=data.model_dump_json())
    return QueryResponse(**res.json())


def format_json(data):
    """Helper function to format JSON with indentation and sorting"""
    return json.dumps(data, indent=2, sort_keys=True)


def log_separator(title=""):
    """Creates a visually distinct separator in logs"""
    separator = "=" * 50
    if title:
        title = f" {title} "
        padding = "=" * ((50 - len(title)) // 2)
        separator = f"{padding}{title}{padding}"
        if len(separator) < 50:  # Ensure consistent length
            separator += "="
    return f"\n{separator}\n"


def send_s05e04(
        url: str,
        task: str,
        apikey: str,
        answer: str | List[Any] | Dict,
        timeout: int = 30,
        max_retries: int = 3,
        just_update: bool = False,
):
    """Send task solution for verification with enhanced structured logging.

    Args:
        url (str): Verification URL
        task (str): Task ID
        apikey (str): API key
        answer (str | List[Any] | Dict): Task solution
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts
        just_update (bool): Bool var to ask directly gpt-4o-mini
    """

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _send_with_retry():
        try:
            # 1. Request Preparation
            logger.info(log_separator("REQUEST PREPARATION"))
            payload = QueryRequestS05E04(
                task=task,
                apikey=apikey,
                answer=answer,
                justUpdate=just_update
            )

            logger.info("Request Details:")
            logger.info(f"→ URL: {url}")
            logger.info(f"→ Task: {task}")
            logger.info(f"→ Payload:\n{format_json(payload.model_dump())}")

            # 2. Sending Request
            logger.info(log_separator("SENDING REQUEST"))
            with httpx.Client(timeout=timeout) as client:
                logger.info("Initiating HTTP POST request...")
                response = client.post(url, json=payload.model_dump())

                # 3. Response Processing
                logger.info(log_separator("RESPONSE RECEIVED"))
                logger.info("Basic Response Info:")
                logger.info(f"→ Status Code: {response.status_code}")
                logger.info(f"→ Response Time: {response.elapsed.total_seconds():.2f}s")

                logger.info("\nResponse Headers:")
                for key, value in response.headers.items():
                    logger.info(f"→ {key}: {value}")

                # 4. Response Content
                logger.info(log_separator("RESPONSE CONTENT"))
                try:
                    json_response = response.json()
                    logger.info("Parsed JSON Response:")
                    logger.info(f"\n{format_json(json_response)}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse JSON response: {str(e)}")
                    logger.info("Raw Response Text:")
                    logger.info(response.text)

                # 5. Status Check
                response.raise_for_status()
                return json_response

        except httpx.HTTPStatusError as e:
            logger.error(log_separator("HTTP ERROR"))
            logger.error(f"HTTP {e.response.status_code} Error:")
            logger.error(f"→ URL: {e.request.url}")
            logger.error(f"→ Method: {e.request.method}")
            logger.error(f"→ Response: {e.response.text}")
            raise

        except Exception as e:
            logger.error(log_separator("UNEXPECTED ERROR"))
            logger.error(f"Type: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            raise

    try:
        logger.info(log_separator("STARTING REQUEST PROCESS"))
        result = _send_with_retry()
        logger.info(log_separator("REQUEST COMPLETED SUCCESSFULLY"))
        return result

    except Exception as e:
        logger.error(log_separator("FINAL ERROR"))
        logger.error(f"Failed after {max_retries} attempts:")
        logger.error(f"→ Error Type: {type(e).__name__}")
        logger.error(f"→ Error Message: {str(e)}")
        logger.exception("Detailed traceback:")
        raise Exception(f"Failed to send data after {max_retries} attempts: {str(e)}")