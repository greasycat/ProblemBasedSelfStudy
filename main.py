import os
import tomllib
from warnings import warn

from textbook import LazyTextbookReader, LLM, TextBookContext

def load_config() -> dict:
    if not os.path.exists("config.toml"):
        warn("config.toml file not found, using default config")
        return {}

    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        warn(f"Error loading config.toml file: {e}")
        return {}
    

def main():
    config = load_config()
    db_path = config.get("db_path", "textbook_context.db")
    
    llm = LLM()
    with TextBookContext(db_path=db_path) as context:
        with LazyTextbookReader("tests/textbooks/topology_scan.pdf", llm, context) as reader:
            reader.extract_book_info()
            reader.extract_toc()
            pass


if __name__ == "__main__":
    main()
