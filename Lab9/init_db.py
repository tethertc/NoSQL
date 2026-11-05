import config
from pymongo import MongoClient

books_data = [
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "year": 1937, "isbn": "9780261103344"},
    {"title": "1984", "author": "George Orwell", "category": "Dystopian", "year": 1949, "isbn": "9780451524935"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "category": "Fiction", "year": 1960, "isbn": "9780446310789"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Classic", "year": 1925, "isbn": "9780743273565"},
    {"title": "Brave New World", "author": "Aldous Huxley", "category": "Dystopian", "year": 1932, "isbn": "9780060850524"},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury", "category": "Dystopian", "year": 1953, "isbn": "9781451673319"},
    {"title": "The Fellowship of the Ring", "author": "J.R.R. Tolkien", "category": "Fantasy", "year": 1954, "isbn": "9780261102354"},
    {"title": "Dune", "author": "Frank Herbert", "category": "Sci-Fi", "year": 1965, "isbn": "9780441172719"},
    {"title": "Neuromancer", "author": "William Gibson", "category": "Sci-Fi", "year": 1984, "isbn": "9780441569595"},
    {"title": "Foundation", "author": "Isaac Asimov", "category": "Sci-Fi", "year": 1951, "isbn": "9780553293357"},
    {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "category": "Classic", "year": 1866, "isbn": "9780140449136"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "category": "Fiction", "year": 1951, "isbn": "9780316769488"},
    {"title": "The Silmarillion", "author": "J.R.R. Tolkien", "category": "Fantasy", "year": 1977, "isbn": "9780618391110"},
    {"title": "Snow Crash", "author": "Neal Stephenson", "category": "Sci-Fi", "year": 1992, "isbn": "9780553380958"},
    {"title": "Animal Farm", "author": "George Orwell", "category": "Dystopian", "year": 1945, "isbn": "9780451526342"}
]

def seed():
    client = MongoClient(config.MONGODB_URI)
    db = client[config.DB_NAME]
    db.books.drop() # Сброс коллекции
    db.books.create_index("isbn", unique=True)
    db.books.insert_many(books_data)
    print("Successfully seeded 15 test items into MongoDB!")

if __name__ == "__main__":
    seed()
