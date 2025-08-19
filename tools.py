# tools.py
from langchain_core.tools import tool

@tool
def check_stock_availability(book_title: str) -> str:
    """Checks if a specific book is currently in stock at Book Nook (mocked)."""
    mock_stock_db = {
        "dracula": 5,
        "the midnight library": 3,
        "project hail mary": 0,
        "sherlock holmes": 8,
    }
    key = book_title.lower()
    for title, count in mock_stock_db.items():
        if title in key:
            return (
                f"Good news! We have {count} copies of '{book_title}' in stock."
                if count > 0
                else f"'{book_title}' is currently out of stock, but we can order it for you."
            )
    return (
        f"I couldn't find '{book_title}' in our system. "
        "Can you check the spelling or provide the author?"
    )

@tool
def get_author_info(author_name: str) -> str:
    """Provides a brief biography for a given author (mocked)."""
    mock_author_db = {
        "bram stoker": "Bram Stoker (1847–1912) was an Irish author, best known for 'Dracula' (1897).",
        "sir arthur conan doyle": "Sir Arthur Conan Doyle (1859–1930) created Sherlock Holmes and was a physician.",
        "agatha christie": "Agatha Christie (1890–1976) wrote 66 detective novels (Poirot, Miss Marple).",
    }
    return mock_author_db.get(
        author_name.lower(),
        f"I don't have info on {author_name} right now, but I can search for their works.",
    )

# Convenience export for create_react_agent
tools = [check_stock_availability, get_author_info]
