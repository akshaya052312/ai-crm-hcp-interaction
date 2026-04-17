"""
Agents package — LangGraph-powered CRM agent.

Exports:
    crm_agent  — Compiled LangGraph runnable
    ALL_TOOLS  — List of all 5 LangChain tools
"""

from app.agents.graph import crm_agent
from app.agents.tools import ALL_TOOLS

__all__ = ["crm_agent", "ALL_TOOLS"]
