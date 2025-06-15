from utils.memory import add_to_memory
from utils.calendar import add_event
from datetime import datetime

def decide_action(input_dict):
    message = input_dict.get("message", "")
    if "remember" in message.lower():
        return "memory"
    elif "schedule" in message.lower() or "meeting" in message.lower():
        return "calendar"
    else:
        return "respond"

def handle_memory(input_dict):
    message = input_dict.get("message", "")
    add_to_memory(f"user_input_{datetime.now().isoformat()}", message)
    return {"response": "Noted and saved to memory."}

def handle_calendar(input_dict):
    message = input_dict.get("message", "")
    add_event(f"Event from message: {message}", "unknown")
    return {"response": "Event saved to your calendar."}

def handle_fallback(input_dict):
    return {"response": "Got it. How can I help you further?"}
