import telebot
import os
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand, BotCommandScope
from database import (create_db, create_settings_table, create_prompts_table, add_user_to_database,
                      find_user_data, update_user_data, delete_settings, find_current_session,
                      find_text_by_role_and_user_id, find_latest_prompt, delete_process_answer, count_users)
from config import make_prompt, MAX_SESSIONS, MAX_TOKENS_IN_SESSION, MAX_USERS
from gpt import GPT
import logging
gpt = GPT()
load_dotenv()

token = os.getenv("BOT_TOKEN")
admin_id = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(token=token)

create_db()
create_prompts_table()
create_settings_table()
# --------------------------------------------------Клавиатура----------------------------------------------------------

main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Создать историю!")
main_menu_keyboard.add("Статистика", "История целиком")


# ----------------------------------------------------------------------------------------------------------------------
def check_user(table_name, user_id, message=None):
    if not find_user_data(table_name, user_id):
        if table_name == "prompts":
            if count_users() == MAX_USERS:
                bot.send_message(message.chat.id, "Достигнут лимит пользователей. Приходите позже.")
                return False
            return True
        add_user_to_database(table_name, user_id)
    return True


def check_processing_answer(user_id, message):
    data = find_user_data("settings", user_id)
    if data:
        if data['processing_answer'] == 1:
            logging.debug("попытка задать еще один вопрос, когда нейросеть уже генерирует другой")

            bot.reply_to(message, "Нейросеть уже придумывает историю для вас. Если хотите что-то добавить, сначала"
                                  " дождитесь ответа от нее.")
            return True
    return False


@bot.message_handler(commands=["start"])
def start_bot(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    if check_processing_answer(user_id, message):
        return

    commands = [  # Установка списка команд с областью видимости и описанием
        BotCommand('start', 'запуск бота'),
        BotCommand('help', 'основная информация о боте'),
        BotCommand('delete_process_resp', 'исправить ошибку работы с нейросетью'),
        BotCommand('debug', 'исправить ошибку работы с нейросетью')
    ]

    bot.set_my_commands(commands)
    BotCommandScope('private', chat_id=message.chat.id)

    bot.send_message(message.chat.id, "Приветики! Я бот, с нейросетью yandexgpt под капотом. С моей помощью вы"
                                      " сможете создавать истории с разными персонажами, жанрами и вселенными.\n\n"
                                      'Наверное не терпится начать? Тогда жмите на кнопку "Создать историю!"\n\n'
                                      'Так как я использую платные ресурсы для взаимодействия с нейросетью, то у вас'
                                      ' <b>ограниченное количество попыток</b> для взаимодействия со мной.\n\n'
                                      'Используйте /help, чтобы узнать больше.', reply_markup=main_menu_keyboard,
                     parse_mode="html")


@bot.message_handler(commands=["help"])
def about_bot(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    if check_processing_answer(user_id, message):
        return
    bot.send_message(message.chat.id, 'Так как я использую платные ресурсы для взаимодействия с нейросетью, то у вас'
                                      ' <b>ограниченное количество попыток</b> для взаимодействия со мной.\n\n'
                                      'Как только нейросеть начинает генерировать историю '
                                      '(после нажатия на кнопку "Начнем!"), вы <b>начинаете сессию.</b>\n\n'
                                      f'<b>Максимальное количество сессий:</b> {MAX_SESSIONS}\n'
                                      f'После того, как они потрачены, вы больше <b>не сможете взаимодействовать с '
                                      f'нейросетью</b>.\n\n'
                                      f'Каждая сессия ограничена по количеству токенов (т.е. объему текста, который вы'
                                      f' можете отправить и получить).\n\n'
                                      f'<b>Максимальное количество токенов в сессии:</b> {MAX_TOKENS_IN_SESSION}.\n'
                                      f'Как только этот <b>лимит исчерпан, сессия завершается.</b> '
                                      f' Но, если у вас еще остались'
                                      f' сессии, то вы <b>можете продолжить вашу историю в новой сессии.</b>\n\n'
                                      f'Информацию о том, сколько ресурсов вы уже потратили, вы сможете найти, нажав '
                                      f'на кнопку <b>"Статистика"</b>.\n\n'
                                      f'<b>История целиком</b> - покажет вашу последнюю созданную историю целиком.\n\n'
                                      f'<b>Создать историю</b> - начните создание истории. (сессия не начинается)',
                     reply_markup=main_menu_keyboard, parse_mode="html")


@bot.message_handler(content_types=["text"], func=lambda message: message.text.lower() == "создать историю!")
def make_genre(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    if check_processing_answer(user_id, message):
        return

    if find_current_session(user_id) + 1 > MAX_SESSIONS:
        bot.send_message(message.chat.id, "Вы исчерпали лимит сессий! Возвращайтесь позже.",
                         reply_markup=main_menu_keyboard)
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Комедия", "Боевик")
    keyboard.add("Хоррор", "Драма")
    keyboard.add("Выход")
    bot.send_message(message.chat.id, "Для начала создания истории выберите <b>жанр</b> из предложенных:",
                     parse_mode="html", reply_markup=keyboard)

    delete_settings("settings", user_id)
    check_user("settings", user_id)
    bot.register_next_step_handler(message, make_character)


def make_character(message, is_next_step=False):
    if message.text not in ["Комедия", "Боевик", "Хоррор", "Драма"] and not is_next_step:
        if message.text.lower() == "выход":
            bot.send_message(message.chat.id, "Подготовка к созданию истории остановлена. Если хотите начать "
                                              'создание новой истории, нажмите на кнопку "Создать историю!"',
                             reply_markup=main_menu_keyboard)
            return

        bot.send_message(message.chat.id, "Кажется, вы выбрали что-то не то. Попробуйте снова!")
        make_genre(message)
        return
    elif message.text in ["Комедия", "Боевик", "Хоррор", "Драма"]:
        user_id = message.from_user.id

        check_user("settings", user_id)
        update_user_data("settings", user_id=user_id, column_name="genre", value=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Луффи", "Робби Локамп")
    keyboard.add("Лара Крофт", "Мейбл Пайнз")
    keyboard.add("Начать сначала")
    bot.send_message(message.chat.id, "Супер! А что насчет <b>персонажа</b>?\n\n"
                                      "<b>Луффи</b> - добрый и смелый парень, молодой пират, "
                                      "который идет к своей цели несмотря ни на что."
                                      " Он больше человек сердца, а не разума, "
                                      "но это не мешает ему успешно строить"
                                      " свой жизненный путь. (One Piece)\n\n"
                                      '<b>Робби Локамп</b> - персонаж из книги Э. М. '
                                      'Ремарка "Три товарища". Он хороший '
                                      'механик и разбирается в машинах. У него есть проблемы с алкоголем и агрессией,'
                                      'вызванные трудным прошлым - участием в войне.\n\n'
                                      '<b>Лара Крофт</b> - известный археолог-авантюрист, '
                                      'на ищет приключений зачастую в '
                                      'очень опасных местах — древних руинах, гробницах, и на пути ее подстерегают '
                                      'множество ловушек и пазлов, а также множество самых разных врагов\n\n'
                                      '<b>Мейбл Пайнз</b> - жизнерадостная, энергичная, '
                                      'полна энтузиазма и свободно-настроена '
                                      '12-летняя девочка. Она относится к жизни просто и непредвзято. '
                                      'Любит подурачиться.(Гравити Фолз) ', reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(message, make_place)


def make_place(message, is_next_step=False):
    if message.text not in ["Луффи", "Робби Локамп", "Лара Крофт", "Мейбл Пайнз"] and not is_next_step:
        if check_restart(message):
            return
        bot.send_message(message.chat.id, "Кажется, вы выбрали что-то не то. Попробуйте снова!")
        make_character(message, True)
        return
    elif message.text in ["Луффи", "Робби Локамп", "Лара Крофт", "Мейбл Пайнз"]:
        user_id = message.from_user.id

        check_user("settings", user_id)
        update_user_data("settings", user_id=user_id, column_name="character", value=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Океан", "Затерянный остров")
    keyboard.add("Катастрофа")
    keyboard.add("Начать сначала")
    bot.send_message(message.chat.id, "Теперь выберите <b>место событий:</b>\n\n"
                                      "<b>Океан</b> - действия разворачиваются на корабле в океане далеко от суши.\n\n"
                                      "<b>Катастрофа</b> - сюжет описывает ситуацию в момент "
                                      "глобальной катастрофы, которая поставила "
                                      "под вопрос существование человечества.\n\n"
                                      "<b>Затерянный остров</b> — это невероятный и "
                                      "таинственный остров. "
                                      "Он был случайно открыт группой исследователей, "
                                      "которых сильный шторм вынес к берегам острова.",
                     reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(message, add_info)


def add_info(message, is_next_step=False):
    if message.text not in ["Океан", "Катастрофа", "Затерянный остров"] and not is_next_step:
        if check_restart(message):
            return
        bot.send_message(message.chat.id, "Кажется, вы выбрали что-то не то. Попробуйте снова!")
        make_place(message, True)
        return
    elif message.text in ["Океан", "Катастрофа", "Затерянный остров"]:
        user_id = message.from_user.id

        check_user("settings", user_id)
        update_user_data("settings", user_id=user_id, column_name="place", value=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Начинаем!")
    keyboard.add("Начать сначала")

    user_id = message.from_user.id
    settings_data = find_user_data("settings", user_id)
    bot.send_message(message.chat.id, 'Конфигурация на данный момент:\n\n'
                                      f'<b>Жанр:</b> {settings_data["genre"]}\n\n'
                                      f'<b>Персонаж:</b> {settings_data["character"]}\n\n'
                                      f'<b>Сеттинг:</b> {settings_data["place"]}\n\n'
                                      f'Если хотите изменить конфигурацию, нажмите на кнопку "Начать сначала"\n\n'
                                      "Кажется, я готов к созданию истории для вас! Если хотите что-то добавить,"
                                      ' просто напишите. В ином случае, нажмите на кнопку "Начинаем!" для начала'
                                      ' генерации истории.\n\n', reply_markup=keyboard, parse_mode="html")

    bot.register_next_step_handler(message, check_ans)


def check_ans(message):
    user_id = message.from_user.id
    if message.text.lower() == "начинаем!":
        if not find_user_data("prompts", user_id):
            session_id = 1
        else:
            prompts_data = find_current_session(user_id)
            session_id = prompts_data + 1
        start_generating(message, session_id)
        return

    if check_restart(message):
        return

    check_user("settings", user_id)
    settings_data = find_user_data("settings", user_id)

    bot.send_message(message.chat.id, 'Отлично! Учту!\n\n Что-то еще? Если нет, нажмите на кнопку "Начинаем!"')

    info = settings_data["additional_info"]

    if info:
        info += ", " + message.text
    else:
        info += message.text
    info += ". "
    update_user_data("settings", user_id=user_id, column_name="additional_info", value=info)

    bot.register_next_step_handler(message, check_ans)


def check_restart(message):
    if message.text.lower() == "начать сначала":
        make_genre(message)
        return True
    return False


def start_generating(message, session_id):
    if not message.text:
        bot.send_message(message.chat.id, "Кажется, вы отправили не текстовый запрос. Я пока не знаю как работать"
                                          "с такими. Пожалуйста, отправьте текстовый запрос.")
        bot.register_next_step_handler(message, start_generating, session_id)
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Завершить историю")

    if message.text == "Продолжить историю в новой сессии":

        session_id += 1

    if session_id > MAX_SESSIONS:
        bot.send_message(message.chat.id, "Вы исчерпали лимит сессий! Возвращайтесь позже.",
                         reply_markup=main_menu_keyboard)
        return

    prompt = message.text

    if prompt == "Выход":
        bot.send_message(message.chat.id, 'Хорошо! Чтобы создать новую историю, нажмите на кнопку "Создать историю!"',
                         reply_markup=main_menu_keyboard)
        return

    if prompt == "История целиком":
        whole_story(message)
        bot.register_next_step_handler(message, start_generating, session_id)
        return

    user_id = message.from_user.id

    if session_id > find_current_session(user_id):  # если начата новая сессия
        if prompt == "Начинаем!":
            mode = "start"
            settings_data = find_user_data("settings", user_id)
            prompt = make_prompt(settings_data)  # создание промпта по заданным параметрам
            special_mode = False
            text = "Начал генерацию истории! Ожидайте..."

        else:   # если при лимите токенов запрашивается продолжение истории в новой сессии
            if prompt == "Продолжить историю в новой сессии":
                bot.send_message(message.chat.id, "Можете продолжить вашу историю.", reply_markup=keyboard)
                bot.register_next_step_handler(message, start_generating, session_id)
                return
            special_mode = True
            if prompt == "Завершить историю":
                mode = "end"
                text = "Отлично! Уже придумываю завершение..."

            else:
                mode = "continue"
                keyboard.add("История целиком")
                text = "Отлично! Уже придумываю продолжение..."

    elif prompt == "Завершить историю":
        mode = "end"
        special_mode = False
        text = "Отлично! Уже придумываю завершение..."
    else:
        mode = "continue"
        keyboard.add("История целиком")
        special_mode = False
        text = "Отлично! Уже придумываю продолжение..."

    msg = bot.send_message(message.chat.id, text, reply_markup=ReplyKeyboardRemove())
    bot.send_chat_action(message.chat.id, action="TYPING")

    update_user_data("settings", user_id, "processing_answer", 1)

    answer = gpt.ask_gpt(prompt, mode, session_id, user_id, special_mode=special_mode)

    update_user_data("settings", user_id, "processing_answer", 0)

    bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    tokens_in_session = find_latest_prompt(user_id)["tokens"]
    if not answer or tokens_in_session > MAX_TOKENS_IN_SESSION:  # если достигнут лимит токенов

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Выход")
        answer = find_text_by_role_and_user_id(user_id, "assistant")

        text = f"<b> Текущая история целиком</b> (сессия {session_id}/{MAX_SESSIONS}):\n\n{answer}"

        if session_id != MAX_SESSIONS:  # если сессий достаточно для продолжения
            keyboard.add("Продолжить историю в новой сессии")
            text += ('\n\n\nНажав на кнопку "Продолжить историю в новой сессии", вы перейдете в следующую сессию, но '
                     'ваша история продолжится.\n\n')

        bot.send_message(message.chat.id, "У вас закончились токены для этой сессии! Сессий осталось: "
                                          f"{MAX_SESSIONS - session_id}.",
                         reply_markup=keyboard)

        bot.send_message(message.chat.id, text, parse_mode="html")

        bot.register_next_step_handler(message, start_generating, session_id)
        return

    bot.send_message(message.chat.id, f"<b>История</b> (сессия {session_id}/{MAX_SESSIONS}):\n\n{answer}",
                     parse_mode="html", reply_markup=keyboard)  # отправка ответа нейросети

    if message.text == "Завершить историю" or prompt == "Завершить историю":
        bot.send_message(message.chat.id, "Вот и вся история!", reply_markup=main_menu_keyboard)
        return

    if tokens_in_session > MAX_TOKENS_IN_SESSION - 100:
        bot.send_message(message.chat.id, f"Вы приближаетесь к лимиту токенов: "
                                          f"<b>{tokens_in_session}/{MAX_TOKENS_IN_SESSION}</b>", parse_mode="html")

    elif tokens_in_session > MAX_TOKENS_IN_SESSION/2:
        bot.send_message(message.chat.id, f"Вы потратили больше половины токенов: "
                                          f"<b>{tokens_in_session}/{MAX_TOKENS_IN_SESSION}</b>", parse_mode="html")

    bot.register_next_step_handler(message, start_generating, session_id)


@bot.message_handler(content_types=["text"], func=lambda message: message.text.lower() == "история целиком")
def whole_story(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    if check_processing_answer(user_id, message):
        return

    story = find_text_by_role_and_user_id(user_id, "assistant")
    if not story:
        story = ('У вас пока <b>нет ни одной</b> готовой истории. '
                 'Чтобы создать одну, нажмите на кнопку "Создать историю!"')
    else:
        story = "<b>Предоставляю вам вашу последнюю историю целиком:</b>\n\n" + story
    bot.send_message(message.chat.id, story, parse_mode="html")


@bot.message_handler(content_types=["text"], func=lambda message: message.text.lower() == "статистика")
def send_stats(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    prompt_data = find_latest_prompt(user_id)
    if not prompt_data:
        bot.send_message(message.chat.id, "Предоставляю вам вашу статистику:\n\n"
                                          f"<b>Сессий израсходовано:</b> 0\n\n"
                                          f"<b>Максимальное количество сессий:</b> {MAX_SESSIONS}\n\n"
                                          f"Вы еще не начинали <b>ни одной сессии</b>, поэтому и токены пока <b>не "
                                          f"тратили.</b>\n\n"
                                          f"<b>Максимальное количество токенов в сессии:</b> {MAX_TOKENS_IN_SESSION}",
                         parse_mode="html")
        return

    bot.send_message(message.chat.id, "Предоставляю вам вашу статистику:\n\n"
                                      f"<b>Сессий израсходовано:</b> {prompt_data['session_id']}\n\n"
                                      f"<b>Максимальное количество сессий:</b> {MAX_SESSIONS}\n\n"
                                      f"<b>В последней сессии</b> вы потратили <b>{prompt_data['tokens']}</b> "
                                      f"токенов.\n\n"
                                      f"<b>Максимальное количество токенов в сессии:</b> {MAX_TOKENS_IN_SESSION}",
                     parse_mode="html")


# на случай, если бот был перезапущен во время исполнения запроса к нейросети
@bot.message_handler(commands=["delete_process_resp"])
def delete_process_resp(message):
    user_id = message.from_user.id
    if user_id == admin_id:
        delete_process_answer()
        bot.send_message(message.chat.id, "Ошибка успешно исправлена.")
    else:
        bot.send_message(message.chat.id, "Доступ запрещен.")


CONTENT_TYPES = ["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice"]


@bot.message_handler(content_types=CONTENT_TYPES)
def any_msg(message):
    user_id = message.from_user.id
    if not check_user("prompts", user_id, message=message):  # если достигнут лимит пользователей
        return

    if check_processing_answer(user_id, message):
        return
    bot.send_message(message.chat.id, 'Отлично сказано! Если хотите создать новую историю, '
                                      'то сначала нажмите на кнопку "Создать историю!"',
                     reply_markup=main_menu_keyboard)


bot.infinity_polling()
