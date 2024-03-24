import requests
import os
from dotenv import load_dotenv
from config import GPT_MODEL
load_dotenv()

token = os.getenv("GPT_TOKEN")
folder_id = os.getenv("FOLDER_ID")


def count_tokens(collection) -> int:
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        "modelUri": f"gpt://{folder_id}/{GPT_MODEL}/latest",
        "maxTokens": 800,
        "messages": []
    }

    for row in collection:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["text"]
            }
        )

    result = requests.post(
        url='https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion',
        headers=headers,
        json=data
    ).json()
    if result:
        result = result['tokens']
    return len(result)
