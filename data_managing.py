import json
import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime

from config import DATABASE


def db_execute(query: str) -> None:
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    con.close()


def db_get(mode, *identifier) -> Optional:
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    if mode == 'one':
        cur.execute(f"""SELECT * FROM user_info WHERE {identifier[0]} = {identifier[1]}""")
        data = cur.fetchone()
    else:
        cur.execute(f"""SELECT {identifier[0]} FROM user_info""")
        data = cur.fetchall()
        data = [i[0] for i in data]
    con.close()
    return data


def save_hubs(user_id: str, hubs: List[str]) -> None:
    if check_user_in_db(user_id):
        return edit_hubs(user_id, hubs)
    data = json.dumps(hubs)
    db_execute(f"""INSERT INTO user_info(user_id, topics, last_update) 
                   VALUES ('{user_id}', '{data}', '{datetime.now()}')""")


def edit_hubs(user_id: str, hubs: List[str]) -> None:
    data = json.dumps(hubs)
    db_execute(f"""UPDATE user_info SET topics = '{data}' WHERE user_id = '{user_id}'""")


def delete_user(user_id: str) -> None:
    db_execute(f"""DELETE FROM user_info WHERE user_id = '{user_id}'""")


def update_date(user_id: str) -> None:
    db_execute(f"""UPDATE user_info SET last_update = '{datetime.now()}' WHERE user_id = '{user_id}'""")


def get_hubs_and_update(user_id: str) -> Tuple[List, datetime]:
    data = db_get('one', 'user_id', user_id)
    return json.loads(data[2]), datetime.fromisoformat(data[3])


def check_user_in_db(user_id: str) -> bool:
    return True if db_get('one', 'user_id', user_id) else False


def fetch_users():
    return db_get('all', 'user_id')
