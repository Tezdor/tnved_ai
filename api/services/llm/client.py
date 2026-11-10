import os

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("PROXYAPI_API_KEY"),
    base_url="https://api.proxyapi.ru/v1"
)