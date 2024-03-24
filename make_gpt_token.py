import json
import os
import time

import requests

TOKEN_PATH = "~/Kolyasik_stories/token"


def create_new_token():
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}

    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
        else:
            print(f"Не удалось получить токен. Статус код: {response.status_code}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


def get_creds():
    try:
        with open(TOKEN_PATH, "r") as f:
            data = json.load(f)
            expiration = data["expires_at"]
        if expiration < time.time():
            create_new_token()
    except:
        create_new_token()

    with open(TOKEN_PATH, "r") as f:
        data = json.load(f)
        token = data["access_token"]

    return token
