# ezhil/app.py
import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage # Import ToolMessage
from utils.memory import get_all_memory, search_memory, add_to_memory, AddMemoryInput
from utils.calendar import get_all_events, add_event, search_events, AddEventInput, SearchEventInput
from langgraph_agent.planner import build_graph
from langchain_core.agents import AgentFinish # Import AgentFinish

# Load environment variables and build the agent
load_dotenv()
ezhi_agent = build_graph()

st.set_page_config(page_title="Ezhil - AI Life Assistant", layout="wide")
st.title("🧠 Ezhil - AI Life Assistant")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="Hi! I'm Ezhil. How can I help you today?")]

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message.type):
        # We need to handle BaseMessage types; AgentFinish does not have .type
        if hasattr(message, 'content'): # Check if it has 'content' attribute (AIMessage, HumanMessage, ToolMessage)
            st.markdown(message.content)
        elif isinstance(message, AgentFinish):
            st.markdown(message.return_values.get("output", "Agent finished its task."))
        else: # Fallback for unexpected types
            st.markdown(str(message))


# Handle user input from chat
if prompt := st.chat_input("What can I help you with?"):
    # Add user message to history and display it
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("human"):
        st.markdown(prompt)

    # Invoke the agent with only the latest user message for the first step
    with st.spinner("Thinking..."):
        inputs = {"messages": [HumanMessage(content=prompt)]}
        final_state = ezhi_agent.invoke(inputs)

        # Iterate through the newly generated messages and append them to session state
        # LangGraph's invoke will return ALL messages generated during that run,
        # starting from the initial input through any tool calls and the final response.
        # We only want to append the *new* messages to avoid duplicates and
        # manage the conversation flow correctly.
        # A simpler way: the final_state['messages'] should contain the full current history
        # We want to display just the *last* AI message.

        # Find the last message that is either an AIMessage or AgentFinish
        response_message = None
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) or isinstance(msg, AgentFinish):
                response_message = msg
                break
        
        # If no AIMessage or AgentFinish is found (e.g., if it ended with a ToolMessage),
        # this indicates a continuing process, and we might just show a "thinking..." or
        # default response, or show the last tool output. For simplicity, let's ensure
        # something is always shown.
        if response_message is None:
             response_message = AIMessage(content="I'm processing that. Please wait or ask another question.")


    # Add AI response to history and display it
    st.session_state.messages.append(response_message)
    with st.chat_message("ai"):
        if hasattr(response_message, 'content'):
            st.markdown(response_message.content)
        elif isinstance(response_message, AgentFinish):
            st.markdown(response_message.return_values.get("output", "Agent finished its task."))
        else:
            st.markdown(str(response_message)) # Fallback for any other type

# --- Sidebar for Tools ---
st.sidebar.header("🛠️ Tools")

if st.sidebar.button("View Calendar"):
    st.sidebar.subheader("Your Calendar Events:")
    events = get_all_events()
    if events:
        st.sidebar.json(events, expanded=False)
    else:
        st.sidebar.info("No events found.")

if st.sidebar.button("View Memory"):
    st.sidebar.subheader("Your Memory:")
    memory = get_all_memory()
    if memory:
        st.sidebar.json(memory, expanded=False)
    else:
        st.sidebar.info("No memory stored.")