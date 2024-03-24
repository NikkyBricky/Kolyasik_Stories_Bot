import logging
import sqlite3


def create_db():
    connection = sqlite3.connect("sqlite3.db")
    connection.close()
    logging.info("База данных успешно создана")


def process_query(query, params):
    connection = sqlite3.connect("sqlite3.db")
    connection.row_factory = sqlite3.Row
    cur = connection.cursor()
    if not params:
        if 'SELECT' in query:
            result = cur.execute(query)
            return result
        cur.execute(query)
    else:
        if 'SELECT' in query:
            result = cur.execute(query, tuple(params))
            return list(result)
        cur.execute(query, tuple(params))
    connection.commit()
    connection.close()


def create_prompts_table():
    query = '''
    CREATE TABLE IF NOT EXISTS prompts(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    role INTEGER,
    text TEXT DEFAULT " ",
    tokens INTEGER DEFAULT 0,
    session_id INTEGER DEFAULT 0);'''
    process_query(query, None)


def create_settings_table():
    query = '''
       CREATE TABLE IF NOT EXISTS settings(
       id INTEGER PRIMARY KEY,
       user_id INTEGER UNIQUE,
       genre TEXT DEFAULT "",
       character TEXT DEFAULT "",
       place TEXT DEFAULT "",
       additional_info TEXT DEFAULT "",
       processing_answer INTEGER DEFAULT 0) ;'''
    process_query(query, None)


def add_user_to_database(table_name, user_id):
    query = f'''INSERT INTO {table_name} (user_id) VALUES (?);'''
    process_query(query, [user_id])
    logging.info(f"Пользователь с user_id = {user_id} успешно добавлен в базу данных")


def find_user_data(table_name, user_id):
    query = f'''SELECT * FROM {table_name} WHERE user_id = ?;'''
    result = process_query(query, [user_id])
    if result:
        logging.info(f"Данные пользователя с user_id {user_id} успешно найдены.")
        return result[0]
    logging.error("Не получилось собрать данные пользователя.")
    return result


def update_user_data(table_name, user_id, column_name, value):
    query = f'''UPDATE {table_name} SET {column_name} = ? WHERE user_id = ?;'''
    process_query(query, [value, user_id])
    logging.info(f"база данных успешно обновлена, колонка: {column_name}, user_id - {user_id}")


def count_users():
    query = "SELECT COUNT(DISTINCT user_id) FROM prompts"
    counter = list(process_query(query, None))
    return counter[0][0]


def find_current_session(user_id):
    query = f'''SELECT COUNT(DISTINCT session_id) FROM prompts WHERE user_id = ?;'''
    counter = process_query(query, [user_id])
    return counter[0][0]


def find_prompts_by_session(user_id, session_id):
    query = "SELECT role, text FROM prompts WHERE user_id = ? and session_id = ?"
    prompts = process_query(query, [user_id, session_id])
    return prompts


def find_assistant_text_by_session(user_id, session_id):
    query = '''
    SELECT text 
    FROM prompts
    WHERE user_id = ? and session_id = ? and role = "assistant" 
    ORDER BY id DESC 
    LIMIT 1'''
    content = process_query(query, [user_id, session_id])
    if content:
        content = content[0]["text"]
    return content


def find_text_by_role_and_user_id(user_id, role):
    query = '''
       SELECT text 
       FROM prompts
       WHERE user_id = ? and role = ?
       ORDER BY id DESC 
       LIMIT 1'''
    content = process_query(query, [user_id, role])
    if content:
        content = content[0]["text"]
    return content


def add_prompt_to_database(user_id, role, text, tokens, session_id):
    query = '''INSERT INTO prompts (user_id, role, text, tokens, session_id) VALUES(?, ?, ?, ?, ?)'''
    values = [user_id, role, text, tokens, session_id]
    process_query(query, values)


def find_latest_prompt(user_id):
    query = f"SELECT * FROM prompts WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    prompt_data = process_query(query, [user_id])
    if prompt_data:
        prompt_data = prompt_data[0]
    return prompt_data


def delete_settings(table_name, user_id):
    query = f"DELETE FROM {table_name} WHERE user_id = ?"
    process_query(query, [user_id])
    logging.info(f"Пользователь с user_id = {user_id} успешно удален из базы данных")


def delete_process_answer():
    query = "UPDATE settings SET processing_answer = 0"
    process_query(query, None)
