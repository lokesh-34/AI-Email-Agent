# ============================================================
# AGENT ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException

from backend.models import AgentChatRequest

from agent import run_agent

router = APIRouter()


@router.post("/api/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """
    Chat with the AI agent.

    Sends a message to the agent and returns
    the response along with updated conversation history.
    """

    try:
        # Filter conversation history to only include
        # serializable message dicts
        history = request.conversation_history or []

        clean_history = []
        for msg in history:
            if isinstance(msg, dict):
                if msg.get("role") in [
                    "user", "assistant", "tool"
                ]:
                    clean_history.append(msg)

        response, updated_history = run_agent(
            request.message,
            clean_history
        )

        # Clean history for serialization
        serializable_history = []
        for msg in updated_history:
            if isinstance(msg, dict):
                serializable_history.append(msg)
            elif hasattr(msg, 'model_dump'):
                serializable_history.append(
                    msg.model_dump()
                )
            else:
                # Skip system message (index 0)
                continue

        # Remove system message from returned history
        if (
            serializable_history
            and serializable_history[0].get("role") == "system"
        ):
            serializable_history = serializable_history[1:]

        return {
            "response": response,
            "conversation_history": serializable_history
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
