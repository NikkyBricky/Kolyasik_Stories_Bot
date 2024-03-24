SYSTEM_PROMPT = (
    "Ты отличный сценарист.\n"
    "Ты пишешь историю вместе с человеком.\n "
    "Историю вы пишете по очереди. Начинает человек, а ты продолжаешь.\n "
    "Если это уместно, ты можешь добавлять в историю диалог между персонажами.\n "
    "Диалоги пиши с новой строки и отделяй тире.\n "
    "Не пиши никакого пояснительного текста в начале, а просто логично начинай историю."
)

CONTINUE_PROMPT = ("Продолжи сюжет в 1-3 предложения и оставь интригу.\n"
                   "Для продолжения используй информацию, переданную пользователем.\n"
                   "Не пиши никакой пояснительный текст от себя")

END_PROMPT = "Напиши завершение истории c неожиданной развязкой. Не пиши никакой пояснительный текст от себя."


def make_prompt(settings_data):
    prompt = (f"\nНапиши начало истории в стиле {settings_data['genre']} "
              f"с главным героем {settings_data['character']}. "
              f"Вот начальный сеттинг: \n{settings_data['place']}. \n"
              "Начало должно быть коротким, 1-3 предложения.\n")
    if settings_data["additional_info"]:
        prompt += (f"Также пользователь попросил учесть "
                   f"следующую дополнительную информацию: {settings_data['additional_info']} ")

    return prompt


MAX_USERS = 3
MAX_SESSIONS = 3
MAX_TOKENS_IN_SESSION = 1000
MAX_MODEL_TOKENS = 250
GPT_MODEL = 'yandexgpt-lite'
TEMPERATURE = 0.3
URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
