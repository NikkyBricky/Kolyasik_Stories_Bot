import logging

import requests
import os
from dotenv import load_dotenv
from config import GPT_MODEL
from make_gpt_token import get_creds
load_dotenv()


def get_token():
    token = os.getenv("GPT_TOKEN")
    if not token:
        token = get_creds()
    return token


folder_id = os.getenv("FOLDER_ID")


def count_tokens(collection) -> int:
    token = get_token()
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

    try:
        result = result['tokens']
        logging.error("Токены для промпта успешно подсчитаны.")
        return len(result)
    except KeyError:
        logging.error("Не удалось посчитать токены для промпта, так как токен недействителен.")
