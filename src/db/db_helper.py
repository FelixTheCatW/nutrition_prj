import psycopg2
from dataclasses import fields, is_dataclass
from typing import Any, Type, Union, Dict, List, Optional, get_type_hints

# Маппинг типов Python в типы PostgreSQL
TYPE_MAPPING = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "BOOLEAN",
    # можно добавить другие: datetime, Decimal и т.д.
}


def _get_persistent_fields(cls: Type) -> list[tuple]:
    """
    Возвращает список кортежей (имя_поля, тип_питон) для полей, которые должны быть в БД.
    Для dataclass исключаются поля с init=False.
    Для обычных классов берутся все аннотированные поля (если есть __annotations__).
    """
    if is_dataclass(cls):
        persistent = []
        for f in fields(cls):
            if f.init:  # только те, что участвуют в __init__
                persistent.append((f.name, f.type))
        return persistent
    else:
        # Обычный класс – используем __annotations__
        hints = get_type_hints(cls)
        # Исключаем служебные имена, если нужно
        return [(name, typ) for name, typ in hints.items() if not name.startswith("_")]


def _py_type_to_sql(py_type: Type) -> str:
    """Преобразует Python тип в строку SQL-типа."""
    # Для Optional, Union и т.п. можно взять первый не-None тип
    origin = getattr(py_type, "__origin__", None)
    if origin in (list, dict, set):  # базово, для сложных типов – JSON или TEXT
        return "JSONB"
    # Для Optional[X] -> X
    if origin is Union and type(None) in py_type.__args__:
        args = [a for a in py_type.__args__ if a is not type(None)]
        if args:
            py_type = args[0]
    return TYPE_MAPPING.get(py_type, "TEXT")


def create_table_from_class(conn: psycopg2.extensions.connection, cls: Type) -> None:
    """
    Создаёт таблицу на основе аннотаций класса.
    Имя таблицы = cls.__name__.lower().
    Поле 'id' делается первичным ключом.
    """
    table_name = cls.__name__.lower()
    persistent_fields = _get_persistent_fields(cls)
    columns = []
    for name, py_type in persistent_fields:
        sql_type = _py_type_to_sql(py_type)
        if name == "id":
            columns.append(f"{name} {sql_type} PRIMARY KEY")
        else:
            columns.append(f"{name} {sql_type}")
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
    with conn.cursor() as cur:
        cur.execute(create_sql)
        conn.commit()


def insert(conn: psycopg2.extensions.connection, instance: Any) -> None:
    """
    Вставляет экземпляр в таблицу, используя только сохраняемые поля.
    """
    cls = type(instance)
    table_name = cls.__name__.lower()
    persistent_fields = _get_persistent_fields(cls)
    columns = [f[0] for f in persistent_fields]
    values = [getattr(instance, name) for name in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    with conn.cursor() as cur:
        cur.execute(insert_sql, values)
        conn.commit()


def update(conn: psycopg2.extensions.connection, instance: Any) -> None:
    """
    Обновляет запись по id.
    Поле id должно существовать и быть сохранённым.
    """
    cls = type(instance)
    table_name = cls.__name__.lower()
    persistent_fields = _get_persistent_fields(cls)
    id_value = None
    updates = []
    values = []
    for name, _ in persistent_fields:
        val = getattr(instance, name)
        if name == "id":
            id_value = val
        else:
            updates.append(f"{name} = %s")
            values.append(val)
    if id_value is None:
        raise ValueError("Нет поля 'id' для обновления")
    values.append(id_value)
    update_sql = f"UPDATE {table_name} SET {', '.join(updates)} WHERE id = %s"
    with conn.cursor() as cur:
        cur.execute(update_sql, values)
        conn.commit()


def delete(conn: psycopg2.extensions.connection, cls: Type, id_value: int) -> None:
    """
    Удаляет запись из таблицы по id.
    """
    table_name = cls.__name__.lower()
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table_name} WHERE id = %s", (id_value,))
        conn.commit()


def select_by_id(conn: psycopg2.extensions.connection, cls: Type, id_value: int) -> Optional[Any]:
    """
    Выбирает запись по id и возвращает новый экземпляр класса,
    заполняя его поля через setattr.
    Поля, отсутствующие в результате SELECT (например, вычисляемые), не трогаются.
    """
    table_name = cls.__name__.lower()
    persistent_fields = _get_persistent_fields(cls)
    columns = [f[0] for f in persistent_fields]
    select_sql = f"SELECT {', '.join(columns)} FROM {table_name} WHERE id = %s"
    with conn.cursor() as cur:
        cur.execute(select_sql, (id_value,))
        row = cur.fetchone()
        if not row:
            return None
        # Создаём экземпляр без вызова __init__ (чтобы не требовать обязательные поля)
        # Для dataclass можно использовать cls.__new__ + setattr, но будет пропущена инициализация.
        # Простой способ: создать пустой объект и заполнить.
        # Если класс имеет __init__ с параметрами, то проблемы – лучше использовать dataclass.
        # Предположим, что класс поддерживает создание через __new__ и setattr (dataclass с default значениями или обычный)
        instance = cls.__new__(cls)
        for col, val in zip(columns, row):
            setattr(instance, col, val)
        return instance


# Пример использования с dataclass
if __name__ == "__main__":
    from dataclasses import dataclass, field

    @dataclass
    class Person:
        id: int
        name: str
        age: int
        weight_kg: float
        # вычисляемое поле – не сохраняется
        bmr: float = field(init=False, default=0.0)

    # Подключение к БД
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="testdb", user="postgres", password="secret"
    )

    # Создание таблицы
    create_table_from_class(conn, Person)

    # Вставка
    p1 = Person(id=1, name="Alice", age=30, weight_kg=65.0)
    insert(conn, p1)

    # Обновление
    p1.age = 31
    update(conn, p1)

    # Выборка
    loaded = select_by_id(conn, Person, 1)
    print(loaded)  # Person(id=1, name='Alice', age=31, weight_kg=65.0, bmr=0.0)

    # Удаление
    delete(conn, Person, 1)

    conn.close()
