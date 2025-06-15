import json
from rapidfuzz import process

def search_memory(query, top_k=3):
    memory_store = load_memory()
    if not memory_store:
        return []

    results = process.extract(query, memory_store.items(), limit=top_k)
    # Each result: ((key, value), score, _)
    matches = []
    for (key, value), score, _ in results:
        matches.append((key, value, score))
    return matches

def load_memory():
    try:
        with open("memory_store.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_memory(data):
    with open("memory_store.json", "w") as f:
        json.dump(data, f, indent=2)

memory_store = load_memory()

def set_memory(key, value):
    memory_store[key] = value
    save_memory(memory_store)
    return f"Memory stored: {key} : {value}"

def add_to_memory(key, value):
    return set_memory(key, value)

def add_to_memory(key, value):
    return set_memory(key, value)

def get_all_memory():
    return memory_store
