from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError
from typing import List, Optional
from models import BookCreate, BookUpdate

class DatabaseConnectionError(Exception):
    """Исключение при недоступности СУБД."""
    pass

class BookNotFoundError(Exception):
    """Исключение, если документ не найден."""
    pass

class BookDuplicateError(Exception):
    """Исключение при нарушении уникальности ISBN."""
    pass

class BookRepository:
    def __init__(self, uri: str, db_name: str):
        try:
            # Устанавливаем таймаут соединения в 2000мс для быстрой генерации 503 ошибки
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[db_name]
            self.collection = self.db["books"]
            # Создаем уникальный индекс по бизнес-ключу isbn
            self.collection.create_index("isbn", unique=True)
        except PyMongoError:
            raise DatabaseConnectionError()

    def _check_connection(self):
        try:
            self.client.admin.command('ping')
        except PyMongoError:
            raise DatabaseConnectionError("Хранилище временно недоступно")

    def create(self, book_data: BookCreate) -> dict:
        self._check_connection()
        try:
            data = book_data.model_dump()
            self.collection.insert_one(data)
            return self.get_by_isbn(data["isbn"])
        except DuplicateKeyError:
            raise BookDuplicateError(f"Книга с ISBN {book_data.isbn} уже зарегистрирована")
        except PyMongoError:
            raise DatabaseConnectionError()

    def get_by_isbn(self, isbn: str) -> dict:
        self._check_connection()
        try:
            book = self.collection.find_one({"isbn": isbn}, {"_id": 0})
            if not book:
                raise BookNotFoundError(f"Книга с ISBN {isbn} не найдена")
            return book
        except PyMongoError:
            raise DatabaseConnectionError()

    def update(self, isbn: str, book_data: BookUpdate) -> dict:
        self._check_connection()
        try:
            update_data = {k: v for k, v in book_data.model_dump().items() if v is not None}
            if not update_data:
                return self.get_by_isbn(isbn)

            result = self.collection.update_one({"isbn": isbn}, {"$set": update_data})
            if result.matched_count == 0:
                raise BookNotFoundError(f"Книга с ISBN {isbn} не найдена")
            return self.get_by_isbn(isbn)
        except PyMongoError:
            raise DatabaseConnectionError()

    def delete(self, isbn: str) -> bool:
        self._check_connection()
        try:
            result = self.collection.delete_one({"isbn": isbn})
            if result.deleted_count == 0:
                raise BookNotFoundError(f"Книга с ISBN {isbn} не найдена")
            return True
        except PyMongoError:
            raise DatabaseConnectionError()

    def search(self, author: Optional[str] = None, category: Optional[str] = None) -> List[dict]:
        self._check_connection()
        query = {}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        try:
            cursor = self.collection.find(query, {"_id": 0})
            return list(cursor)
        except PyMongoError:
            raise DatabaseConnectionError()
