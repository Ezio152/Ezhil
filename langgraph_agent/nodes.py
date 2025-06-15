from utils.memory import add_to_memory
from utils.calendar import add_event
from datetime import datetime

def decide_action(state: dict) -> dict:
    message = state.get("message", "").lower()
    if "remember" in message:
        next_node = "memory"
    elif "schedule" in message or "meeting" in message:
        next_node = "calendar"
    else:
        next_node = "respond"
    return {"next": next_node}

def handle_memory(state: dict) -> dict:
    message = state.get("message", "")
    add_to_memory(f"user_input_{datetime.now().isoformat()}", message)
    return {"response": "Noted and saved to memory."}

def handle_calendar(state: dict) -> dict:
    message = state.get("message", "")
    add_event(f"Event from message: {message}", "unknown")
    return {"response": "Event saved to your calendar."}

def handle_respond(state: dict) -> dict:
    return {"response": "Got it. How can I help you further?"}
