import llm
import os

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
TEXT_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("LLM_EMBEDDING_MODEL_NAME", "gemini-embedding-001")
API_KEY = os.getenv("LLM_GEMINI_KEY")
if API_KEY is None:
    raise ValueError("LLM_GEMINI_KEY is not set")

class LLM:
    def __init__(self):
        self.text_model = llm.get_model(TEXT_MODEL_NAME) # type: ignore
        self.embedding_model = llm.get_embedding_model(EMBEDDING_MODEL_NAME) # type: ignore
        self.text_model.key = API_KEY
        self.embedding_model.key = API_KEY

if __name__ == "__main__":
    llm = LLM()
    print(llm.text_model.prompt("Counter the number of R in word strawberry"))
    print(llm.embedding_model.embed("Hello, world!"))