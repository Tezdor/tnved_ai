import json

def clean_json(content):

    content = content.strip()

    content = content.replace("```json", "")
    content = content.replace("```", "")

    start_obj = content.find("{")
    start_arr = content.find("[")

    starts = [
        x
        for x in [start_obj, start_arr]
        if x != -1
    ]

    if not starts:

        raise Exception(
            f"JSON не найден:\n{content}"
        )

    start = min(starts)

    json_text = content[start:]

    decoder = json.JSONDecoder()

    obj, idx = decoder.raw_decode(
        json_text
    )

    return obj
