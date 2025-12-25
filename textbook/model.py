import os
from typing import TypeVar



import llm
import structlog

from pydantic import BaseModel

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
TEXT_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("LLM_EMBEDDING_MODEL_NAME", "gemini-embedding-001")
API_KEY = os.getenv("LLM_GEMINI_KEY")
if API_KEY is None:
    raise ValueError("LLM_GEMINI_KEY is not set")

T = TypeVar("T", bound=BaseModel)

class LLM:
    def __init__(self):
        self.logger = structlog.get_logger("LLM")
        self.text_model = llm.get_model(TEXT_MODEL_NAME) # type: ignore
        self.embedding_model = llm.get_embedding_model(EMBEDDING_MODEL_NAME) # type: ignore
        self.text_model.key = API_KEY
        self.embedding_model.key = API_KEY
        if not self.health_check():
            raise RuntimeError("LLM health check failed")
        else:
            self.logger.info("LLM health check passed")
    
    def prompt_with_schema(self, prompt: str, schema: type[T]) -> T:
        self.logger.debug("Prompting LLM with prompt", prompt=prompt, schema=schema)
        response = self.text_model.prompt(prompt, schema=schema)
        self.logger.debug(f"Response: {response.text()}")
        return schema.model_validate_json(response.text())
    
    def health_check(self) -> bool:
        response = self.text_model.prompt("Where is the capital of France?")
        return "paris" in response.text().lower()

if __name__ == "__main__":
    llm = LLM()
    print(llm.text_model.prompt("Counter the number of R in word strawberry"))
    print(llm.embedding_model.embed("Hello, world!"))