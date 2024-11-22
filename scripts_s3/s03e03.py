import os
from dotenv import load_dotenv

from src.send_task import send
from src.s_03.e_03 import create_sql_agent

if __name__ == "__main__":
    load_dotenv()
    result = create_sql_agent()
    print(f"Final result: {result}")

    answer = [item["dc_id"] for item in result]

    # Send answer
    res = send(
        url=f"{os.environ.get('CENTRALA_URL')}report",
        apikey=os.getenv("API_KEY"),
        answer=answer,
        task="database",
    )
    print(res)
