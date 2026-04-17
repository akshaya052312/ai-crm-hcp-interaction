"""
LangGraph Agent — HCP Interaction Logger

Defines the StateGraph that wires the LLM (with tools bound) into a
ReAct-style agent loop:

    ┌─────────┐       tool_call        ┌───────────┐
    │  agent  │ ─────────────────────▶ │   tools   │
    │  (LLM)  │ ◀───────────────────── │  (execute) │
    └────┬────┘     tool_result        └───────────┘
         │
         │ no tool_call (final answer)
         ▼
       [END]

Flow:
  1. START  → agent_node:   LLM receives messages and decides whether to
                            call a tool or respond directly.
  2. agent  → tools_condition: If the LLM response contains tool calls,
                               route to the "tools" node. Otherwise → END.
  3. tools  → agent_node:  Tool results are appended to messages and the
                            LLM is invoked again to interpret results.
  4. Repeat until the LLM produces a final text response (no tool calls).
"""

import os
from typing import Annotated

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.tools import ALL_TOOLS
from app.agents.prompts import AGENT_SYSTEM_PROMPT

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# LLM Configuration
# ═══════════════════════════════════════════════════════════════
# The agent LLM uses the primary model (gemma2-9b-it) for fast
# tool-routing decisions. Tools themselves may internally use
# the larger context model (llama-3.3-70b-versatile) for heavier
# NLP tasks like summarisation.

agent_llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "gemma2-9b-it"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=4096,
)

# Bind all tools to the LLM so it can generate tool_call messages.
# This tells the LLM about each tool's name, description, and parameters.
agent_llm_with_tools = agent_llm.bind_tools(ALL_TOOLS)


# ═══════════════════════════════════════════════════════════════
# Node Definitions
# ═══════════════════════════════════════════════════════════════

def agent_node(state: MessagesState) -> dict:
    """The 'brain' of the agent — invokes the LLM with the conversation
    history and lets it decide whether to call a tool or respond directly.

    The system prompt is prepended to every invocation to maintain the
    agent's persona and instructions.

    Args:
        state: Current graph state containing the message history.

    Returns:
        Updated messages list with the LLM's response appended.
    """
    from langchain_core.messages import SystemMessage

    # Build the full message list: system prompt + conversation history
    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + state["messages"]

    # Invoke the LLM (with tools bound) — it will either:
    #   a) Return a text response   → routes to END
    #   b) Return tool_call messages → routes to tools node
    response = agent_llm_with_tools.invoke(messages)

    return {"messages": [response]}


# The ToolNode automatically executes whichever tool the LLM requested
# and returns the result as a ToolMessage. It handles all 5 tools:
#   log_interaction, edit_interaction, get_hcp_history,
#   suggest_follow_up, search_hcp
tool_node = ToolNode(ALL_TOOLS)


# ═══════════════════════════════════════════════════════════════
# Graph Construction
# ═══════════════════════════════════════════════════════════════
# Build the state graph following the ReAct (Reasoning + Acting) pattern:
#   - The agent reasons about the user's message
#   - Decides which tool to act with (or responds directly)
#   - Observes the tool result
#   - Reasons again until a final answer is produced

def build_graph():
    """Construct and compile the LangGraph StateGraph.

    Returns:
        A compiled LangGraph runnable that can process messages.
    """
    # Initialise the graph with MessagesState — a built-in state schema
    # that tracks a list of messages (user, AI, tool results)
    graph = StateGraph(MessagesState)

    # ── Add nodes ──────────────────────────────────────────
    # "agent" — the LLM decision-maker
    graph.add_node("agent", agent_node)

    # "tools" — executes the tool the LLM chose
    graph.add_node("tools", tool_node)

    # ── Add edges ──────────────────────────────────────────
    # START → agent: Every conversation begins at the agent node
    graph.add_edge(START, "agent")

    # agent → (conditional): After the LLM responds, check if it
    # wants to call a tool. If yes → "tools" node. If no → END.
    # `tools_condition` is a built-in LangGraph function that
    # inspects the last AI message for tool_calls.
    graph.add_conditional_edges("agent", tools_condition)

    # tools → agent: After a tool executes, loop back to the agent
    # so it can interpret the tool's result and decide what to do next
    # (call another tool, or produce the final response).
    graph.add_edge("tools", "agent")

    # ── Compile ────────────────────────────────────────────
    # Compiling the graph validates the structure and returns a
    # runnable object with .invoke() and .stream() methods.
    compiled = graph.compile()

    return compiled


# ═══════════════════════════════════════════════════════════════
# Compiled Graph Instance
# ═══════════════════════════════════════════════════════════════
# Singleton instance ready for import by the API layer.
# Usage:
#   from app.agents.graph import crm_agent
#   result = crm_agent.invoke({"messages": [HumanMessage(content="...")]})

crm_agent = build_graph()
