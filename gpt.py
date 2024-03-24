import requests
from database import add_prompt_to_database, find_assistant_text_by_session, find_prompts_by_session
from config import SYSTEM_PROMPT, END_PROMPT, CONTINUE_PROMPT, MAX_TOKENS_IN_SESSION, MAX_MODEL_TOKENS
from check_tokens import count_tokens

import os
from dotenv import load_dotenv
from config import GPT_MODEL
load_dotenv()

token = os.getenv("GPT_TOKEN")
folder_id = os.getenv("FOLDER_ID")


class GPT:
    def __init__(self):
        self.URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
        self.HEADERS = {'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'}
        self.TEMPERATURE = 0.5

    def ask_gpt(self, user_content: str, mode: str, session_id: int, user_id: int, special_mode: bool):
        tokens = 0
        prompts_data = find_prompts_by_session(user_id, session_id)
        if prompts_data:
            tokens = count_tokens(prompts_data)

        if mode == "start":
            system_content = SYSTEM_PROMPT
        elif mode in ["continue", "continue_in_new_session"]:
            system_content = CONTINUE_PROMPT
        else:
            system_content = END_PROMPT

        tokens_in_system = count_tokens([{"role": "system", "text": system_content}])
        tokens_in_system += tokens

        add_prompt_to_database(user_id, "system", system_content, tokens_in_system, session_id)

        tokens_in_user_content = count_tokens([{"role": "user", "text": user_content}])
        tokens_in_user_content += tokens_in_system
        add_prompt_to_database(user_id, "user", user_content, tokens_in_user_content, session_id)

        if tokens_in_user_content > MAX_TOKENS_IN_SESSION:
            return
        if special_mode:
            assistant_content = find_assistant_text_by_session(user_id, session_id - 1)
        else:
            assistant_content = find_assistant_text_by_session(user_id, session_id)
        if not assistant_content:
            assistant_content = " "

        data = {
            "modelUri": f"gpt://{folder_id}/{GPT_MODEL}/latest",
            "completionOptions": {
                "stream": False,
                "temperature": self.TEMPERATURE,
                "maxTokens": MAX_MODEL_TOKENS
            },
            "messages": [
                {"role": "system", "text": system_content},
                {"role": "user", "text": user_content},
                {"role": "assistant", "text": assistant_content}
            ]
        }

        result = requests.post(self.URL, headers=self.HEADERS, json=data)
        if 200 <= result.status_code < 400:
            result = result.json()['result']['alternatives'][0]['message']['text']
            tokens_in_assistant_content = count_tokens([{"role": "assistant", "text": result}])
            tokens_in_assistant_content += tokens_in_user_content

            add_prompt_to_database(user_id, "assistant", assistant_content + result,
                                   tokens_in_assistant_content, session_id)
            return result
        return f"Код ошибки: {result.status_code}, Ошибка {result.json()['error']}"
