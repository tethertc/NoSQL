from fastapi import FastAPI, HTTPException, status, Query
from typing import List, Optional
import config
from repository import BookRepository, DatabaseConnectionError, BookNotFoundError, BookDuplicateError
from models import BookCreate, BookUpdate, BookResponse

app = FastAPI(title="Library NoSQL API Service (Вариант 9)")
repo = BookRepository(config.MONGODB_URI, config.DB_NAME)

@app.post("/items", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    try:
        return repo.create(book)
    except BookDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DatabaseConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище временно недоступно")

@app.get("/items/{id}", response_model=BookResponse)
def get_book(id: str):
    try:
        return repo.get_by_isbn(id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище временно недоступно")

@app.get("/items", response_model=List[BookResponse])
def search_books(
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    category: Optional[str] = Query(None, description="Фильтр по категории/жанру")
):
    try:
        return repo.search(author=author, category=category)
    except DatabaseConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище временно недоступно")

@app.put("/items/{id}", response_model=BookResponse)
def update_book(id: str, book_data: BookUpdate):
    try:
        return repo.update(id, book_data)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище временно недоступно")

@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(id: str):
    try:
        repo.delete(id)
        return
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище временно недоступно")
