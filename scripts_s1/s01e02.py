import asyncio
import os
from dotenv import load_dotenv

from src.s_01.e_02 import RobotVerification


async def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    endpoint = os.getenv("S01E02_ENDPOINT")

    verifier = RobotVerification(api_key, endpoint)
    success = await verifier.verify()

    if success:
        verifier.logger.info("Main: Verification successful!")
    else:
        verifier.logger.error("Main: Verification failed!")


# Example usage
if __name__ == "__main__":
    asyncio.run(main())
