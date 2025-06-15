import json
from pathlib import Path
from rapidfuzz import process
from langchain_core.pydantic_v1 import BaseModel, Field

# Define the input schema for the memory tool
class AddMemoryInput(BaseModel):
    key: str = Field(description="A concise, memorable key for the piece of information.")
    value: str = Field(description="The detailed information to be stored.")

MEMORY_FILE = Path(__file__).parent.parent / "memory_store.json"

def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {}

def save_memory(data):
    MEMORY_FILE.write_text(json.dumps(data, indent=2))

# This function is now our "tool"
def add_to_memory(key: str, value: str) -> str:
    """Stores a piece of information for the user to recall later."""
    mem = load_memory()
    mem[key] = value
    save_memory(mem)
    return f"OK, I've stored the following: '{key}: {value}'"

def get_all_memory():
    return load_memory()

# Search function can be improved to search values more effectively
def search_memory(query: str, top_k=3) -> list[tuple[str, str, float]]:
    print(f"[DEBUG] search_memory called with query={query}")
    """Searches through the user's stored memories for relevant information."""
    mem = load_memory()
    if not mem:
        return []
    # Search against the content (values) for better results
    choices = {f"{k}: {v}": (k, v) for k, v in mem.items()}
    results = process.extract(query, choices.keys(), limit=top_k)
    
    # Return a structured result
    return [(choices[item][0], choices[item][1], score) for item, score, _ in results]