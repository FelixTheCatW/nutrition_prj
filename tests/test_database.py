import unittest
import tempfile
import os
import sqlite3
from src.db.database import Database


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Создаём временный файл для тестов
        cls.temp_db = tempfile.NamedTemporaryFile(delete=False)
        cls.db_path = cls.temp_db.name
        cls.temp_db.close()
        Database.connect(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        Database.close()
        os.unlink(cls.db_path)  # удаляем временный файл

    def setUp(self):
        # Создаём таблицу перед каждым тестом
        Database.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                calories REAL,
                protein_g REAL,
                fat_g REAL,
                carbs_g REAL
            )
        """)
        # Очищаем таблицу
        Database.execute("DELETE FROM products")

    def tearDown(self):
        # Удаляем таблицу после каждого теста
        Database.execute("DROP TABLE IF EXISTS products")

    # ---------- Тесты базовых методов ----------
    def test_connect_singleton(self):
        conn1 = Database.connect()
        conn2 = Database.connect()
        self.assertIs(conn1, conn2, "connect() должен возвращать одно и то же соединение")

    def test_execute_insert(self):
        cursor = Database.execute(
            "INSERT INTO products (name, calories) VALUES (?, ?)", ("Тестовый продукт", 100)
        )
        self.assertEqual(cursor.lastrowid, 1)

    def test_execute_rollback_on_error(self):
        # Создаём таблицу с ограничением NOT NULL
        Database.execute("CREATE TABLE IF NOT EXISTS test (id INT, name TEXT NOT NULL)")
        with self.assertRaises(sqlite3.IntegrityError):
            Database.execute("INSERT INTO test (id, name) VALUES (?, ?)", (1, None))
        # Проверяем, что транзакция откатилась и таблица пуста
        count = Database.fetchall("SELECT COUNT(*) as cnt FROM test")[0]["cnt"]
        self.assertEqual(count, 0)
        Database.execute("DROP TABLE test")

    def test_fetchall(self):
        Database.execute(
            "INSERT INTO products (name, calories) VALUES (?, ?), (?, ?)", ("А", 50, "Б", 60)
        )
        rows = Database.fetchall("SELECT * FROM products ORDER BY name")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "А")
        self.assertEqual(rows[1]["calories"], 60)

    def test_fetchall_empty(self):
        rows = Database.fetchall("SELECT * FROM products")
        self.assertEqual(rows, [])

    # ---------- Тесты insert_object / update_object ----------
    def test_insert_object(self):
        class Product:
            def __init__(self, name, calories, protein_g):
                self.name = name
                self.calories = calories
                self.protein_g = protein_g

        p = Product("Сыр", 350, 25)
        product_id = Database.insert_object(p, "products")
        self.assertEqual(product_id, 1)

        row = Database.fetchall("SELECT * FROM products")[0]
        self.assertEqual(row["name"], "Сыр")
        self.assertEqual(row["calories"], 350)
        self.assertEqual(row["protein_g"], 25)
        self.assertIsNone(row["fat_g"])  # не было задано

    def test_insert_object_empty_data(self):
        class Empty:
            pass

        e = Empty()
        with self.assertRaises(ValueError) as ctx:
            Database.insert_object(e, "products")
        self.assertEqual(str(ctx.exception), "Нет данных для вставки")

    def test_update_object(self):
        class Product:
            def __init__(self, id, name, calories):
                self.id = id
                self.name = name
                self.calories = calories

        # Сначала вставляем объект
        Database.execute(
            "INSERT INTO products (id, name, calories) VALUES (?, ?, ?)", (10, "Старый", 100)
        )
        p = Product(10, "Новый", 200)
        rows_updated = Database.update_object(p, "products", key="id")
        self.assertEqual(rows_updated, 1)

        row = Database.fetchall("SELECT name, calories FROM products WHERE id=10")[0]
        self.assertEqual(row["name"], "Новый")
        self.assertEqual(row["calories"], 200)

    def test_update_object_no_data(self):
        class Product:
            def __init__(self, id):
                self.id = id

        p = Product(1)
        # Никаких полей для обновления (только id – исключён)
        with self.assertRaises(ValueError) as ctx:
            Database.update_object(p, "products", key="id")
        self.assertEqual(str(ctx.exception), "Нет данных для обновления")

    def test_update_object_nonexistent(self):
        class Product:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        p = Product(999, "Несуществующий")
        rows_updated = Database.update_object(p, "products", key="id")
        self.assertEqual(rows_updated, 0)  # не обновлено ни одной строки

    # ---------- Тест закрытия соединения ----------
    def test_close_connection(self):
        Database.close()
        self.assertIsNone(Database._connection)
        # Повторное подключение работает
        conn = Database.connect()
        self.assertIsNotNone(conn)


if __name__ == "__main__":
    unittest.main()
