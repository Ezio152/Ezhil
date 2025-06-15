# ezhil/langgraph_agent/planner.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from utils.memory import add_to_memory, AddMemoryInput, search_memory
from utils.calendar import add_event, AddEventInput, search_events, SearchEventInput
from datetime import datetime, date

# --- Tool definitions with mandatory docstrings ---
@tool(args_schema=AddMemoryInput)
def memory_tool(key: str, value: str) -> str:
    """Store a piece of information for the user to recall later. Use a concise, memorable key."""
    return add_to_memory(key, value)

@tool
def search_memory_tool(query: str) -> str:
    """Search through the user's stored memories for relevant information. Provide a concise query."""
    results = search_memory(query)
    if not results:
        return "No relevant memories found."
    # Format results nicely for the user
    formatted_results = "\n".join([f"Key: {k}, Value: {v}" for k, v, _ in results])
    return f"Here's what I found in your memory for '{query}':\n{formatted_results}"

@tool(args_schema=AddEventInput)
def calendar_add_event_tool(
    title: str,
    event_date: str,
    time: str = "all-day",
    description: str = "",
) -> str:
    """Schedules a new event on the user's calendar. Provide title, date (YYYY-MM-DD), time (e.g., '2:00 PM'), and optional description."""
    return add_event(title, event_date, time, description)

@tool(args_schema=SearchEventInput)
def calendar_search_events_tool(query_date: str) -> str:
    """Searches for calendar events based on a specific date (YYYY-MM-DD) or keywords like 'today', 'tomorrow', 'this week'. Use this to check the user's schedule."""
    return search_events(query_date)

# ezhil/langgraph_agent/planner.py
# ... (rest of imports and tool definitions) ...

# --- State type for LangGraph ---
class AgentState(TypedDict):
    """State dict holds a list of BaseMessage (chat history)."""
    messages: Annotated[Sequence[BaseMessage], lambda a, b: a + b]

def build_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1, # Slightly increase temperature for better conversational responses
        convert_system_message_to_human=True
    ).bind_tools([memory_tool, search_memory_tool, calendar_add_event_tool, calendar_search_events_tool])

    tools = [memory_tool, search_memory_tool, calendar_add_event_tool, calendar_search_events_tool]
    tool_node = ToolNode(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are Ezhil—an AI assistant that remembers things and schedules events. Today's date is {date.today().isoformat()}.\n"
            "You MUST use the memory_tool to store any fact the user asks you to remember, and you MUST use the search_memory_tool to answer any question about facts you have stored.\n"
            "Do not answer from your own knowledge, always use the tools for these tasks.\n"
            "When the user asks about their schedule or calendar, use the calendar_search_events_tool.\n"
            "When the user asks to schedule an event, use the calendar_add_event_tool.\n"
            "If no tool is needed, respond conversationally and helpfully and try to answer the question directly. Always respond in a helpful and friendly manner."),
        MessagesPlaceholder("messages"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent_runnable = create_tool_calling_agent(llm, tools, prompt)

    def run_agent(state: AgentState) -> AgentState:
        conversational_messages = []
        agent_scratchpad = []

        for msg in state["messages"]:
            if isinstance(msg, HumanMessage) or (isinstance(msg, AIMessage) and not msg.tool_calls):
                conversational_messages.append(msg)
            elif isinstance(msg, AIMessage) and msg.tool_calls:
                agent_scratchpad.append(msg)
            elif isinstance(msg, ToolMessage):
                agent_scratchpad.append(msg)

        messages_for_agent = conversational_messages # This should always contain the latest user input

        # If agent_scratchpad has content, ensure the model sees previous tool interactions
        # This is crucial for multi-turn tool use.
        if agent_scratchpad:
            # LangGraph's prebuilt agent takes 'intermediate_steps' as a list of tuples (AgentAction, Observation)
            # However, create_tool_calling_agent expects messages in 'agent_scratchpad' placeholder.
            # So, keep feeding AIMessage(tool_calls) and ToolMessage directly.
            pass # The filtering logic above ensures this is handled

        print(f"\n--- RUN AGENT INPUT ---")
        print(f"Messages for LLM: {messages_for_agent}")
        print(f"Agent Scratchpad: {agent_scratchpad}")

        out = agent_runnable.invoke({
            "messages": messages_for_agent,
            "intermediate_steps": []  # Pass an empty list to avoid unpacking errors
        })

        print(f"--- RUN AGENT OUTPUT ---")
        print(f"Output type: {type(out)}, content: {out}")
        if isinstance(out, list):
            return {"messages": state["messages"] + out}
        else:
            return {"messages": state["messages"] + [out]}


    def run_tools(state: AgentState) -> AgentState:
        last_msg = state["messages"][-1]
        print(f"\n--- RUN TOOLS INPUT ---")
        print(f"Last message for tools: {last_msg}")
        from langchain.agents.output_parsers.tools import ToolAgentAction
        if isinstance(last_msg, AIMessage) and getattr(last_msg, 'tool_calls', None):
            tool_outputs = tool_node.invoke(last_msg)
            print(f"--- RUN TOOLS OUTPUT ---")
            print(f"Tool outputs: {tool_outputs}")
            return {"messages": state["messages"] + tool_outputs["messages"]}
        elif isinstance(last_msg, ToolAgentAction):
            tool_outputs = tool_node.invoke(last_msg)
            print(f"--- RUN TOOLS OUTPUT (ToolAgentAction) ---")
            print(f"Tool outputs: {tool_outputs}")
            return {"messages": state["messages"] + tool_outputs["messages"]}
        return state

    def should_call_tools(state: AgentState) -> str:
        last = state["messages"][-1]
        print(f"\n--- SHOULD CALL TOOLS ---")
        print(f"Last message type: {type(last)}, tool_calls: {getattr(last, 'tool_calls', 'N/A')}")
        from langchain.agents.output_parsers.tools import ToolAgentAction
        from langchain_core.messages import ToolMessage
        if (isinstance(last, AIMessage) and getattr(last, 'tool_calls', None)) or isinstance(last, ToolAgentAction):
            return "run_tools"
        if isinstance(last, ToolMessage):
            # If the previous message was also a ToolMessage with the same tool_call_id, END
            if len(state["messages"]) > 1:
                prev = state["messages"][-2]
                if (isinstance(prev, ToolMessage) and prev.tool_call_id == last.tool_call_id):
                    return END
            return "agent"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", run_agent)
    graph.add_node("run_tools", run_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_call_tools)
    graph.add_edge("run_tools", "agent")

    return graph.compile()