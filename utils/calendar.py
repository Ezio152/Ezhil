import json

def load_calendar():
    try:
        with open("calendar_store.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_calendar(data):
    with open("calendar_store.json", "w") as f:
        json.dump(data, f, indent=2)

calendar_store = load_calendar()

def create_event(title, date, time="unknown", description=""):
    event = {"title": title, "date": date, "time": time, "description": description}
    calendar_store.append(event)
    save_calendar(calendar_store)
    return f"Event '{title}' scheduled on {date} at {time}."

def add_event(title, date):
    return create_event(title, date)

def get_all_events():
    return calendar_store
