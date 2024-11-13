import os
import asyncio
import httpx
from bs4 import BeautifulSoup
from src.s_01.e_01 import extract_question, answer_question


async def main():
    base_url = os.getenv("S01E01_ENDPOINT")
    if not base_url:
        print("URL environment variable not set")
        return

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # First request - get the question and login
            response = await client.get(base_url)
            response.raise_for_status()

            question = await extract_question(response.text)
            if not question:
                print("No question found.")
                return

            answer = await answer_question(question)

            login_response = await client.post(
                base_url,
                data={
                    "username": os.getenv("S01E01_USERNAME"),
                    "password": os.getenv("S01E01_PASSWORD"),
                    "answer": answer,
                },
            )
            login_response.raise_for_status()

            # Get firmware page content
            firmware_url = base_url.rstrip("/") + "/firmware"
            firmware_response = await client.get(firmware_url)
            firmware_response.raise_for_status()

            print("\nFirmware page content:")
            print(firmware_response.text)

            # Parse HTML to find download link
            soup = BeautifulSoup(firmware_response.text, "html.parser")
            download_link = soup.find("a", href=True)

            if download_link:
                file_url = base_url.rstrip("/") + download_link["href"]
                print(f"\nDownloading file from: {file_url}")

                # Download the file
                file_response = await client.get(file_url)
                file_response.raise_for_status()

                # Get the filename from the URL
                filename = download_link["href"].split("/")[-1]

                # Save the file
                with open(filename, "wb") as f:
                    f.write(file_response.content)

                print(f"File saved as: {filename}")
                print("\nFile content:")
                print(file_response.text)

                # Extract flag
                flag_element = soup.find(
                    "h2", style="background:#f4ffaa;font-family:monospace"
                )
                if flag_element:
                    print("\nFlag found:")
                    print(flag_element.text)

    except httpx.ConnectError:
        print(f"Failed to connect to {base_url}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
