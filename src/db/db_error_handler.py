import sqlite3
from functools import wraps


def db_error_handler(commit_on_success=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if commit_on_success:
                    args[0]._connection.commit()
                return result
            except sqlite3.Error as e:
                args[0]._connection.rollback()
                print(f"DB error: {e}")
                raise

        return wrapper

    return decorator
