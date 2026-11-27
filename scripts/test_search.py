
import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://www.socialcrawl.dev/v1/twitter/search/tweets"

headers = {
    "x-api-key": os.getenv("SOCIALCRAWL_API_KEY")
}

params = {
    "query": '"E20 petrol" mileage',
    "sort": "latest",
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

print("Status:", response.status_code)
data = response.json()["data"]["items"]
print(data[0])