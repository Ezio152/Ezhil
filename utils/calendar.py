# ezhil/utils/calendar.py
import json
from pathlib import Path
from datetime import date, datetime
from pydantic import BaseModel, Field

# Define the input schema for the calendar tool
class AddEventInput(BaseModel):
    title: str = Field(description="The title or name of the event.")
    event_date: str = Field(description="The date of the event, in YYYY-MM-DD format.")
    time: str = Field(default="all-day", description="The time of the event, e.g., '2:00 PM'.")
    description: str = Field(default="", description="Any extra details about the event.")

class SearchEventInput(BaseModel):
    query_date: str = Field(description="The date to search events for, in YYYY-MM-DD format, or keywords like 'today', 'tomorrow', 'this week'.")

CALENDAR_FILE = Path(__file__).parent.parent / "calendar_store.json"

def load_calendar():
    if CALENDAR_FILE.exists():
        return json.loads(CALENDAR_FILE.read_text())
    return []

def save_calendar(data):
    CALENDAR_FILE.write_text(json.dumps(data, indent=2))

# This function is now our "tool"
def add_event(title: str, event_date: str, time: str = "all-day", description: str = "") -> str:
    """Schedules a new event on the user's calendar."""
    events = load_calendar()
    try:
        # Validate date format
        datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        return f"Error: Invalid date format for '{event_date}'. Please use YYYY-MM-DD. For today, use {date.today().isoformat()}."
    events.append({"title": title, "date": event_date, "time": time, "description": description})
    save_calendar(events)
    return f"Event '{title}' has been successfully scheduled on {event_date} at {time}."

def get_all_events():
    return load_calendar()

def search_events(query_date: str) -> str:
    """Searches for calendar events based on a specific date or keywords like 'today', 'tomorrow', 'this week'."""
    events = load_calendar()
    if not events:
        return "No events found in your calendar."

    today = date.today()
    found_events = []

    # Simple date matching for now, can be expanded for more complex queries
    for event in events:
        event_date_str = event.get("date")
        if not event_date_str:
            continue

        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue # Skip malformed dates

        if query_date.lower() == "today" and event_date == today:
            found_events.append(event)
        elif query_date.lower() == "tomorrow" and event_date == today + timedelta(days=1):
            found_events.append(event)
        elif query_date.lower() == "this week": # Simple check for this week (Mon-Sun)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            if start_of_week <= event_date <= end_of_week:
                found_events.append(event)
        elif query_date == event_date_str:
            found_events.append(event)

    if found_events:
        return "Here are the events found:\n" + "\n".join(
            f"- {e['title']} on {e['date']} at {e['time']} ({e['description']})" for e in found_events
        )
    else:
        return f"No events found for '{query_date}'."

# Add timedelta for 'tomorrow' and 'this week' logic
from datetime import timedelta