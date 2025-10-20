import os
import logging
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_conn():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "Root081284081206!"),
            database=os.getenv("DB_NAME", "breadtalk_pos"),
            autocommit=False,
        )
        logger.info("MySQL connected host=%s db=%s user=%s",
                    os.getenv("DB_HOST"), os.getenv("DB_NAME"), os.getenv("DB_USER"))
        return conn
    except Exception:
        logger.exception("Failed to connect to MySQL")
        raise