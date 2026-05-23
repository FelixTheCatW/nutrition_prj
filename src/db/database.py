import sqlite3
from src.db.db_error_handler import db_error_handler


class Database:
    _connection = None

    @classmethod
    def connect(cls, db_path="nutrition.db"):
        if cls._connection is None:
            cls._connection = sqlite3.connect(db_path)
            cls._connection.row_factory = sqlite3.Row
        return cls._connection

    @classmethod
    @db_error_handler()
    def execute(cls, query, params=()):
        cursor = cls._connection.execute(query, params)
        cls._connection.commit()
        return cursor

    @classmethod
    def fetchall(cls, query, params=()):
        return cls.execute(query, params).fetchall()

    @classmethod
    def close(cls):
        if cls._connection:
            cls._connection.close()
            cls._connection = None

    @staticmethod
    def _obj_to_dict(obj, exclude=("id",)):
        return {k: v for k, v in vars(obj).items() if k not in exclude and v is not None}

    @classmethod
    def insert_object(cls, obj, table_name):
        # Используем _obj_to_dict, чтобы получить словарь
        data_dict = cls._obj_to_dict(obj)
        if not data_dict:
            raise ValueError("Нет данных для вставки")

        columns = ",".join(data_dict.keys())
        placeholders = ",".join(["?"] * len(data_dict))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor = cls.execute(query, list(data_dict.values()))
        return cursor.lastrowid

    @classmethod
    def update_object(cls, obj, table_name, key="id"):
        data_dict = cls._obj_to_dict(obj, exclude=(key,))
        if not data_dict:
            raise ValueError("Нет данных для обновления")
        set_clause = ",".join([f"{k}=?" for k in data_dict])
        values = list(data_dict.values()) + [getattr(obj, key)]
        query = f"UPDATE {table_name} SET {set_clause} WHERE {key}=?"
        return cls.execute(query, values).rowcount
