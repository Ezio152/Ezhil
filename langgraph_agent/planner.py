# langgraph_agent/planner.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableLambda
from langgraph_agent import nodes

def build_graph():
    graph = StateGraph(input=dict, output=dict)

    graph.add_node("router", RunnableLambda(nodes.decide_action))
    graph.add_node("memory", RunnableLambda(nodes.handle_memory))
    graph.add_node("calendar", RunnableLambda(nodes.handle_calendar))
    graph.add_node("respond", RunnableLambda(nodes.handle_fallback))

    graph.set_entry_point("router")

    graph.add_edge("router", "memory")
    graph.add_edge("router", "calendar")
    graph.add_edge("router", "respond")
    graph.add_edge("memory", END)
    graph.add_edge("calendar", END)
    graph.add_edge("respond", END)

    return graph.compile()
