
import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("SOCIALCRAWL_API_KEY")

response = requests.get(
    "https://www.socialcrawl.dev/v1/credits/balance",
    headers={"x-api-key": key},
    timeout=20
)

print("Status:", response.status_code)
print(response.json())
