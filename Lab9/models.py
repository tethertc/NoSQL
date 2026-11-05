from pydantic import BaseModel, Field
from typing import Optional

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, description="Название книги")
    author: str = Field(..., min_length=1, description="Автор книги")
    category: str = Field(..., min_length=1, description="Категория/Жанр")
    year: int = Field(..., gte=0, description="Год издания")
    isbn: str = Field(..., min_length=10, description="Уникальный номер книги (вместо ID)")

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1)
    year: Optional[int] = Field(None, gte=0)
    isbn: Optional[str] = Field(None, min_length=10)

class BookResponse(BookBase):
    pass
