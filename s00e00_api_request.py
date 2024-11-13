import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

ENDPOINT = "https://poligon.aidevs.pl/verify"
API_KEY = os.environ["API_KEY"]
TASK_NAME = "POLIGON"


def get_data_from_website():
    url = "https://poligon.aidevs.pl/dane.txt"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip().split("\n")
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")


# Function to send POST request
def send_post_request(data):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "task": TASK_NAME,
        "apikey": API_KEY,
        "answer": data
    }
    response = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload))
    return response

# Main execution
try:
    # Get the two strings from the website
    strings = get_data_from_website()
    if len(strings) != 2:
        raise Exception("Expected 2 strings, but got a different number")

    # Send the POST request
    response = send_post_request(strings)

    # Check the response
    if response.status_code == 200:
        print("Success! Response:", response.json())
    else:
        print(f"Failed with status code: {response.status_code}")
        print("Response:", response.text)

except Exception as e:
    print(f"An error occurred: {str(e)}")
