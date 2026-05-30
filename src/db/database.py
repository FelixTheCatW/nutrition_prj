import os
import logging
from contextlib import contextmanager
from psycopg2 import pool, Error as PGError
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class Database:
    _pool = None

    @classmethod
    def initialize(cls, config: dict):
        """Вызвать один раз при старте приложения."""
        if cls._pool is None:
            cls._pool = pool.SimpleConnectionPool(
                minconn=config.get("min_conn", 1),
                maxconn=config.get("max_conn", 10),
                dbname=config["dbname"],
                user=config["user"],
                password=config["password"],
                host=config["host"],
                port=config["port"],
            )

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Получить соединение из пула (автоматически возвращает в пул)."""
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def cursor(cls, commit=False):
        """Контекстный менеджер для курсора с автоматическим commit/rollback."""
        with cls.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except PGError as e:
                conn.rollback()
                logger.error(f"DB error: {e}")
                raise
            finally:
                cursor.close()

    @classmethod
    def execute(cls, query, params=None, commit=True):
        """Простое выполнение запроса (без выборки)."""
        with cls.cursor(commit=commit) as cur:
            cur.execute(query, params)
            return cur.rowcount

    @classmethod
    def fetch_one(cls, query, params=None):
        """Вернуть одну запись (словарь) или None."""
        with cls.cursor(commit=False) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    @classmethod
    def fetch_all(cls, query, params=None):
        """Вернуть список записей (словарей)."""
        with cls.cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @classmethod
    def insert(cls, table, data: dict, returning="id"):
        """Вставка словаря и возврат ID."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING {returning}"
        with cls.cursor(commit=True) as cur:
            cur.execute(query, list(data.values()))
            return cur.fetchone()[returning]

    @classmethod
    def update(cls, table, data: dict, where: str, where_params=None):
        """Обновление по условию."""
        set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
        params = list(data.values())
        if where_params:
            params.extend(where_params)
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        return cls.execute(query, params, commit=True)
