import streamlit as st
import os
from dotenv import load_dotenv

from utils.memory import get_all_memory
from utils.calendar import get_all_events
from langgraph_agent.planner import build_graph

ezhil_agent = build_graph()

load_dotenv()

st.set_page_config(page_title="Ezhil - Your AI Assistant", layout="centered")
st.title("🧠 Ezhil - AI Life Assistant")

st.markdown("Talk to Ezhil about your life, schedule events, or remember things!")

# Add buttons to view calendar and memory
event_view = st.button("View Calendar")
memory_view = st.button("View Memory")

if event_view:
    events = get_all_events()
    if events:
        st.subheader("Your Calendar Events:")
        st.table(events)
    else:
        st.info("No events found.")

if memory_view:
    memory = get_all_memory()
    if memory:
        st.subheader("Your Memory:")
        st.json(memory)
    else:
        st.info("No memory stored.")

user_input = st.text_input("Ask Ezhil something:")
if st.button("Ask Ezhil") and user_input:
    # Use the new agent to process input
    state = {}
    result = ezhil_agent.invoke({"message": user_input, "state": state})
    st.success(f"Ezhil: {result.get('response', 'No response')}")

with st.expander("🔍 Search My Memories"):
    from utils.memory import search_memory
    query = st.text_input("What should I search in memory?")
    if st.button("Search Memory") and query:
        matches = search_memory(query)
        if not matches:
            st.info("No relevant memory found.")
        else:
            for key, value, score in matches:
                st.write(f"🧠 {key}: {value} (match: {int(score)}%)")
