import os
import tomllib
from warnings import warn

from textbook import LazyTextbookReader, LLM, TextBookDatabase
from pathlib import Path

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
    with TextBookDatabase(db_path=db_path) as context:
        with LazyTextbookReader(Path("tests/textbooks/topology_scan.pdf"), llm, context) as reader:
            reader.update_book_info()
            reader.update_toc()
            reader.update_alignment_offset(page_number=15)
            # reader.interactive_alignment_offset()
            reader.check_alignment_offset()

if __name__ == "__main__":
    main()
