import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "Root081284081206!"),
        database=os.getenv("DB_NAME", "breadtalk_pos"),
        autocommit=False,
    )