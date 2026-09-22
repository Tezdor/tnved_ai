import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


URL = "http://127.0.0.1:8000/api/analyze-product/"


USERS = [
    {
        "name": "USER_1",
        "description": "кружка керамическая",
        "answers": [
            {
                "question": "Из какого материала изготовлена кружка?",
                "answer": "Керамика"
            },
            {
                "question": "Имеет ли кружка какие-либо специальные покрытия или отделку?",
                "answer": "Да"
            },
            {
                "question": "Какой объем кружки?",
                "answer": "Менее 200 мл"
            },
            {
                "question": "Предназначена ли кружка для использования в микроволновой печи?",
                "answer": "Да"
            }
        ]
    },
    {
        "name": "USER_2",
        "description": "шарф из шерсти",
        "answers": [
            {
                "question": "Из какого материала изготовлен шарф?",
                "answer": "Шерсть"
            },
            {
                "question": "Для кого предназначен товар?",
                "answer": "Для взрослых"
            },
            {
                "question": "Является ли товар частью комплекта?",
                "answer": "Нет"
            }
        ]
    },
    {
        "name": "USER_3",
        "description": "сковорода алюминиевая с антипригарным покрытием",
        "answers": [
            {
                "question": "Из какого материала изготовлена сковорода?",
                "answer": "Алюминий"
            },
            {
                "question": "Имеет ли сковорода антипригарное покрытие?",
                "answer": "Да"
            },
            {
                "question": "Для какого использования предназначена сковорода?",
                "answer": "Для бытового использования"
            }
        ]
    },
    {
        "name": "USER_4",
        "description": "футболка мужская хлопковая",
        "answers": [
            {
                "question": "Из какого материала изготовлена футболка?",
                "answer": "Хлопок"
            },
            {
                "question": "Для кого предназначен товар?",
                "answer": "Для взрослых мужчин"
            },
            {
                "question": "Является ли товар частью комплекта?",
                "answer": "Нет"
            }
        ]
    },
    {
        "name": "USER_5",
        "description": "солнцезащитные очки пластиковые",
        "answers": [
            {
                "question": "Из какого материала изготовлены очки?",
                "answer": "Пластик"
            },
            {
                "question": "Для чего предназначен товар?",
                "answer": "Для защиты глаз от солнца"
            },
            {
                "question": "Является ли товар частью комплекта?",
                "answer": "Нет"
            }
        ]
    }
]


def send_request(user):
    name = user["name"]

    payload = {
        "description": user["description"],
        "vision_data": None,
        "answers": user["answers"]
    }

    print(f"[{name}] START: {user['description']}")

    start_time = time.time()

    try:
        response = requests.post(
            URL,
            json=payload,
            timeout=180
        )

        elapsed = time.time() - start_time

        print(
            f"[{name}] FINISH: "
            f"HTTP {response.status_code}, "
            f"{elapsed:.2f} сек."
        )

        try:
            data = response.json()
        except Exception:
            data = None

        if isinstance(data, dict):
            if "final" in data:
                final = data["final"]

                print(
                    f"[{name}] FINAL: "
                    f"{final.get('recommended_code')} | "
                    f"confidence={final.get('confidence')} | "
                    f"supported_by={final.get('supported_by')}"
                )

            if data.get("error"):
                print(f"[{name}] ERROR: {data['error']}")

        return {
            "name": name,
            "status": response.status_code,
            "time": elapsed,
            "data": data
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time

        print(
            f"[{name}] TIMEOUT "
            f"после {elapsed:.2f} сек."
        )

        return {
            "name": name,
            "status": "TIMEOUT",
            "time": elapsed,
            "data": None
        }

    except Exception as e:
        elapsed = time.time() - start_time

        print(
            f"[{name}] EXCEPTION: "
            f"{type(e).__name__}: {e}"
        )

        return {
            "name": name,
            "status": "EXCEPTION",
            "time": elapsed,
            "data": None
        }


print("=" * 70)
print("LOAD TEST: 5 CONCURRENT USERS")
print("=" * 70)

test_start = time.time()

results = []

with ThreadPoolExecutor(max_workers=5) as executor:

    futures = [
        executor.submit(send_request, user)
        for user in USERS
    ]

    for future in as_completed(futures):
        result = future.result()
        results.append(result)


total_time = time.time() - test_start


print()
print("=" * 70)
print("TEST FINISHED")
print("=" * 70)

print(f"Общее время теста: {total_time:.2f} сек.")
print()

for result in sorted(results, key=lambda x: x["name"]):
    print(
        f"{result['name']}: "
        f"status={result['status']}, "
        f"time={result['time']:.2f} сек."
    )

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

successful = sum(
    1 for r in results
    if r["status"] == 200
)

timeouts = sum(
    1 for r in results
    if r["status"] == "TIMEOUT"
)

exceptions = sum(
    1 for r in results
    if r["status"] == "EXCEPTION"
)

print(f"Успешных запросов: {successful}/5")
print(f"TIMEOUT: {timeouts}")
print(f"EXCEPTION: {exceptions}")
print(f"Общее время: {total_time:.2f} сек.")