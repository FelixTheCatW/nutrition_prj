import re
import logging
from contextlib import contextmanager
from typing import Any, Type, Union
import dataclasses

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
    def executemany(cls, query, params_list, commit=True):
        with cls.cursor(commit=commit) as cur:
            if "RETURNING" in query.upper():
                raise NotImplementedError(
                    "executemany с RETURNING не поддерживается. Используйте insert_instances."
                )
            else:
                cur.executemany(query, params_list)
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
        cls.execute(query, params, commit=True)

    @classmethod
    def _get_persistent_fields(cls, cls_type: Type) -> list[tuple[str, Type]]:
        if dataclasses.is_dataclass(cls_type):
            persistent = []
            for f in dataclasses.fields(cls_type):
                if f.init:
                    persistent.append((f.name, f.type))
            return persistent
        else:            
            hints = getattr(cls_type, "__annotations__", {})
            return [(name, typ) for name, typ in hints.items() if not name.startswith("_")]

    @classmethod
    def _py_type_to_sql(cls, py_type: Type) -> str:        
        # Обработка Optional / Union
        origin = getattr(py_type, "__origin__", None)
        if origin is Union:            
            args = [a for a in py_type.__args__ if a is not type(None)]
            if args:
                py_type = args[0]
                origin = getattr(py_type, "__origin__", None)

        mapping = {
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
            bool: "BOOLEAN",
            list: "JSONB",
            dict: "JSONB",
        }

        if origin in (list, dict):
            return "JSONB"
        return mapping.get(py_type, "TEXT")

    @classmethod
    def _to_snake_case(cls, name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @classmethod
    def _table_name(cls, cls_type: Type) -> str:
        return cls._to_snake_case(cls_type.__name__)

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
                columns.append(f"{name} SERIAL PRIMARY KEY")
            else:
                columns.append(f"{name} {sql_type}")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        cls.execute(create_sql, commit=True)
        logger.info(f"Таблица {table_name} создана (или уже существует)")

    @classmethod
    def insert_instance(cls, instance: Any) -> int:
        cls_type = type(instance)
        table_name = cls._table_name(cls_type)
        fields = cls._get_persistent_fields(cls_type)

        data = {}
        has_id = False
        for name, _ in fields:
            value = getattr(instance, name)
            if name == "id":
                has_id = True
                continue
            data[name] = value
        print(data)
        generated_id = cls.insert(table_name, data, returning="id")
        # Обновляем атрибут id у экземпляра
        if has_id:
            setattr(instance, "id", generated_id)
        return generated_id

    @classmethod
    def insert_batch(cls, instances: list[Any]) -> None:
        if not instances:
            return
        cls_type = type(instances[0])
        table_name = cls._table_name(cls_type)
        fields = cls._get_persistent_fields(cls_type)
        columns = [name for name, _ in fields if name != "id"]

        rows = []
        for inst in instances:
            rows.append([getattr(inst, name) for name in columns])

        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        cls.executemany(query, rows)

    @classmethod
    def update_instance(cls, instance: Any) -> None:
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
    def delete_by_id(cls, cls_type: Type, id_value: int) -> None:
        """
        Удаляет запись из таблицы, соответствующей классу, по значению id.
        """
        table_name = cls._table_name(cls_type)
        cls.execute(f"DELETE FROM {table_name} WHERE id = %s", (id_value,), commit=True)

    @classmethod
    def select_by_id(cls, cls_type: Type, id_value: int):
        table_name = cls._table_name(cls_type)
        persistent_fields = cls._get_persistent_fields(cls_type)
        if not persistent_fields:
            raise ValueError(f"Нет сохраняемых полей у класса {cls_type.__name__}")

        columns = [name for name, _ in persistent_fields]
        select_sql = f"SELECT {', '.join(columns)} FROM {table_name} WHERE id = %s"
        row = cls.fetch_one(select_sql, (id_value,))
        if not row:
            return None

        instance = cls_type.__new__(cls_type)
        for col in columns:
            setattr(instance, col, row[col])
        return instance

    @classmethod
    def select(cls, cls_type: Type, where: str = None, where_params=None) -> [Type]:
        table_name = cls._table_name(cls_type)
        persistent_fields = cls._get_persistent_fields(cls_type)
        if not persistent_fields:
            raise ValueError(f"Нет сохраняемых полей у класса {cls_type.__name__}")

        params = ()
        if where_params:
            params.extend(where_params)

        columns = [name for name, _ in persistent_fields]
        select_sql = f"SELECT {', '.join(columns)} FROM {table_name} {where}"
        rows = cls.fetch_all(select_sql, (where_params,))
        if not rows:
            return None
        out = []
        for row in rows:
            instance = cls_type.__new__(cls_type)
            for col in columns:
                setattr(instance, col, row[col])
            out.append(instance)
        return out
