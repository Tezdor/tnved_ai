import requests

url = "https://basket-26.wbcontent.net/vol4608/part460856/460856179/info/ru/card.json"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(
    url,
    headers=headers,
    timeout=20,
)

print(r.status_code)
print(r.text[:300])