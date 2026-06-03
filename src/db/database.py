import os
import logging
from contextlib import contextmanager
from typing import Any, Type, List, Tuple, Optional, Union
import dataclasses

import psycopg2
from psycopg2 import pool, Error as PGError
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class Database:
    _pool = None

    @classmethod
    def initialize(cls, config: dict):
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
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def cursor(cls, commit=False):
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
        with cls.cursor(commit=commit) as cur:
            cur.execute(query, params)
            return cur.rowcount

    @classmethod
    def fetch_one(cls, query, params=None):
        with cls.cursor(commit=False) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    @classmethod
    def fetch_all(cls, query, params=None):
        with cls.cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @classmethod
    def insert(cls, table, data: dict, returning="id"):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING {returning}"
        with cls.cursor(commit=True) as cur:
            cur.execute(query, list(data.values()))
            return cur.fetchone()[returning]

    @classmethod
    def update(cls, table, data: dict, where: str, where_params=None):
        set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
        params = list(data.values())
        if where_params:
            params.extend(where_params)
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        return cls.execute(query, params, commit=True)

    # ---------- Новые методы для работы с ORM-подобными классами ----------
    @classmethod
    def _get_persistent_fields(cls, cls_type: Type) -> List[Tuple[str, Type]]:
        """
        Возвращает список (имя_поля, тип_python) полей, которые должны сохраняться в БД.
        Для dataclass исключаются поля с init=False.
        Для обычных классов используются аннотации типов (__annotations__).
        """
        if dataclasses.is_dataclass(cls_type):
            persistent = []
            for f in dataclasses.fields(cls_type):
                if f.init:  # только поля, передаваемые в __init__
                    persistent.append((f.name, f.type))
            return persistent
        else:
            # обычный класс – берём аннотации
            hints = getattr(cls_type, "__annotations__", {})
            return [(name, typ) for name, typ in hints.items() if not name.startswith("_")]

    @classmethod
    def _py_type_to_sql(cls, py_type: Type) -> str:
        """Преобразует Python-тип в SQL-тип PostgreSQL."""
        # Обработка Optional / Union
        origin = getattr(py_type, "__origin__", None)
        if origin is Union:
            # Исключаем None и берём первый не-None тип
            args = [a for a in py_type.__args__ if a is not type(None)]
            if args:
                py_type = args[0]
                origin = getattr(py_type, "__origin__", None)

        # Базовые типы
        mapping = {
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
            bool: "BOOLEAN",
            list: "JSONB",
            dict: "JSONB",
        }
        # Для list/dict (в аннотациях) сработает выше, а для других – generic
        if origin in (list, dict):
            return "JSONB"
        return mapping.get(py_type, "TEXT")

    @classmethod
    def _table_name(cls, cls_type: Type) -> str:        
        return cls_type.__name__.lower()

    @classmethod
    def create_table_for_class(cls, cls_type: Type) -> None:
        """
        Поле 'id' объявляется первичным ключом всегда.
        """
        table_name = cls._table_name(cls_type)
        persistent_fields = cls._get_persistent_fields(cls_type)
        if not persistent_fields:
            raise ValueError(f"Нет сохраняемых полей для класса {cls_type.__name__}")

        columns = []
        for name, py_type in persistent_fields:
            sql_type = cls._py_type_to_sql(py_type)
            if name == "id":
                columns.append(f"{name} {sql_type} PRIMARY KEY")
            else:
                columns.append(f"{name} {sql_type}")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        cls.execute(create_sql, commit=True)
        logger.info(f"Таблица {table_name} создана (или уже существует)")

@classmethod
def insert_instance(cls, instance: Any) -> int:
    """
    Вставляет экземпляр в БД, генерируя id автоматически.
    Возвращает сгенерированный id и обновляет поле instance.id.
    """
    cls_type = type(instance)
    table_name = cls._table_name(cls_type)
    fields = cls._get_persistent_fields(cls_type)

    data = {}
    has_id = False
    for name, _ in fields:
        value = getattr(instance, name)
        if name == "id":
            has_id = True
        data[name] = value

    # Выполняем INSERT с возвратом id
    generated_id = cls.insert(table_name, data, returning="id")
    # Обновляем атрибут id у экземпляра
    if has_id:
        setattr(instance, "id", generated_id)
    return generated_id


@classmethod
def update_instance(cls, instance: Any) -> None:
    """
    Обновляет запись в БД, соответствующую данному экземпляру, по полю id.
    Поле id не изменяется.
    """
    cls_type = type(instance)
    table_name = cls._table_name(cls_type)
    fields = cls._get_persistent_fields(cls_type)

    data = {}
    id_value = None
    for name, _ in fields:
        value = getattr(instance, name)
        if name == "id":
            id_value = value
        else:
            data[name] = value

    if id_value is None:
        raise ValueError("Невозможно обновить запись: поле id отсутствует или равно None")

    cls.update(table_name, data, where="id = %s", where_params=[id_value])


@classmethod
def save_instance(cls, instance: Any) -> int:
    """
    Универсальный метод: если id отсутствует (None или 0), вызывает insert_instance,
    иначе — update_instance. Возвращает id.
    """
    id_val = getattr(instance, "id", None)
    if id_val is None or id_val == 0:
        return cls.insert_instance(instance)
    else:
        cls.update_instance(instance)
        return id_val