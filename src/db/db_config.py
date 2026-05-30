# config.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv


class DBConfig:
    # Атрибуты класса со значениями по умолчанию
    DBNAME = None
    USER = None
    PASSWORD = None
    HOST = None
    PORT = None
    MIN_CONN = None
    MAX_CONN = None

    @classmethod
    def load_from_env(cls, dotenv_path=None):
        """
        Загружает параметры подключения из .env файла.
        Если dotenv_path не указан, ищет .env в текущей директории и выше.
        """
        load_dotenv(dotenv_path=dotenv_path)

        cls.DBNAME = os.getenv("DB_NAME")
        cls.USER = os.getenv("DB_USER")
        cls.PASSWORD = os.getenv("DB_PASSWORD")
        cls.HOST = os.getenv("DB_HOST", "localhost")
        cls.PORT = int(os.getenv("DB_PORT", 5432))
        cls.MIN_CONN = int(os.getenv("DB_MIN_CONN", 1))
        cls.MAX_CONN = int(os.getenv("DB_MAX_CONN", 10))

        # Проверка обязательных параметров
        if not cls.DBNAME or not cls.USER or not cls.PASSWORD:
            raise ValueError(
                "Missing required DB environment variables: DB_NAME, DB_USER, DB_PASSWORD"
            )

    @classmethod
    def as_dict(cls):
        """Возвращает словарь для передачи в Database.initialize()"""
        return {
            "dbname": cls.DBNAME,
            "user": cls.USER,
            "password": cls.PASSWORD,
            "host": cls.HOST,
            "port": cls.PORT,
            "min_conn": cls.MIN_CONN,
            "max_conn": cls.MAX_CONN,
        }

    @classmethod
    def url(cls):
        """
        Возвращает URL подключения в формате:
        postgresql://user:password@host:port/dbname
        Пароль экранируется (например, если содержит @, /, :).
        """
        if not cls.PASSWORD:
            raise RuntimeError("Configuration not loaded. Call load_from_env() first.")

        escaped_password = quote_plus(cls.PASSWORD)
        return f"postgresql://{cls.USER}:{escaped_password}@{cls.HOST}:{cls.PORT}/{cls.DBNAME}"
