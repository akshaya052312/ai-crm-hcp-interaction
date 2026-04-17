"""
Chat Route — /api/chat

Endpoint:
  POST /chat — Send a free-text message through the full LangGraph agent.
               The agent autonomously routes to the appropriate tool(s)
               and returns a conversational response.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agents.graph import crm_agent
from app.models.schemas import APIResponse, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


# ─────────────────────────────────────────────────────────────
# POST /api/chat
# ─────────────────────────────────────────────────────────────

@router.post("", response_model=APIResponse)
async def api_chat(body: ChatRequest):
    """Send a message to the CRM Agent and receive a response.

    The LangGraph agent processes the message, decides whether to
    invoke any of the 5 tools, and returns a final conversational
    response. This is the primary endpoint for the chat interface.

    The agent supports multi-turn reasoning: if a tool call is needed,
    the agent executes it, reads the result, and formulates a
    human-readable reply.
    """
    try:
        # ── Invoke the compiled LangGraph agent ──
        # Wrap the user's message as a HumanMessage and pass it
        # into the agent graph. The graph will loop through
        # agent → tools → agent until a final response is produced.
        result = crm_agent.invoke({
            "messages": [HumanMessage(content=body.message)]
        })

        # ── Extract the final response and tool call info ──
        messages = result.get("messages", [])

        # The last AIMessage without tool_calls is the final reply
        final_reply = ""
        tool_calls_made = []

        for msg in messages:
            # Collect tool names that were called during this turn
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_made.append(tc["name"])

            # The final AI message (without tool calls) is the response
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                final_reply = msg.content

        # Fallback: if no clean final message, use the last message content
        if not final_reply and messages:
            final_reply = messages[-1].content

        chat_response = ChatResponse(
            reply=final_reply,
            tool_calls=tool_calls_made,
        )

        return APIResponse(
            success=True,
            data=chat_response.model_dump(),
            message="Agent response generated",
        )

    except Exception as e:
        logger.exception("Chat agent failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}",
        )
