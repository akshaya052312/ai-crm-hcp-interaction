"""
Unit Tests for the 5 LangGraph Tools — HCP Interaction Logger

Tests each tool with mocked Groq LLM calls and mocked database sessions.
Run with:  pytest backend/tests/test_tools.py -v
"""

import json
import uuid
from datetime import date, time, datetime
from unittest.mock import patch, MagicMock, PropertyMock

import pytest


# ═══════════════════════════════════════════════════════════════
# Fixtures & Helpers
# ═══════════════════════════════════════════════════════════════

def _make_mock_hcp(name="Dr. Sarah Smith", specialty="Cardiology"):
    """Create a mock HCP object."""
    hcp = MagicMock()
    hcp.id = uuid.uuid4()
    hcp.name = name
    hcp.specialty = specialty
    hcp.location = "New York"
    hcp.hospital = "City Hospital"
    hcp.email = None
    hcp.phone = None
    return hcp


def _make_mock_interaction(hcp_id=None, sentiment="positive"):
    """Create a mock Interaction object."""
    interaction = MagicMock()
    interaction.id = uuid.uuid4()
    interaction.hcp_id = hcp_id or uuid.uuid4()
    interaction.interaction_type = "in-person"
    interaction.date = date.today()
    interaction.time = time(10, 30)
    interaction.attendees = "Dr. Smith, Nurse Johnson"
    interaction.topics_discussed = "Product X efficacy"
    interaction.outcomes = "Positive reception"
    interaction.follow_up_actions = "Send Phase III data"
    interaction.sentiment = sentiment
    interaction.created_at = datetime.now()
    interaction.updated_at = datetime.now()
    return interaction


def _make_llm_response(content: str):
    """Create a mock LLM response object with .content attribute."""
    response = MagicMock()
    response.content = content
    return response


# ═══════════════════════════════════════════════════════════════
# TOOL 1 — log_interaction
# ═══════════════════════════════════════════════════════════════

@patch("app.agents.tools.SessionLocal")
@patch("app.agents.tools.PRIMARY_LLM")
def test_log_interaction_success(mock_llm, mock_session_cls):
    """Test that log_interaction parses a note and saves to DB."""
    from app.agents.tools import log_interaction

    # Mock LLM response — structured JSON extraction
    extracted_data = {
        "hcp_name": "Dr. Sarah Smith",
        "specialty": "Cardiology",
        "location": "New York",
        "hospital": "City Hospital",
        "interaction_type": "in-person",
        "date": str(date.today()),
        "time": "10:30",
        "attendees": "Nurse Johnson",
        "topics_discussed": "Product X efficacy and Phase III data",
        "outcomes": "Positive reception, wants to proceed",
        "follow_up_actions": "Send Phase III clinical data",
        "sentiment": "positive",
        "materials_shared": [
            {"material_name": "Clinical Study Brochure", "material_type": "brochure"}
        ],
        "samples_distributed": [
            {"sample_name": "Product X 50mg", "quantity": 3}
        ],
    }
    mock_llm.invoke.return_value = _make_llm_response(json.dumps(extracted_data))

    # Mock DB session
    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing HCP

    # Execute the tool (LangChain tools need .invoke())
    result = log_interaction.invoke({"note": "Met Dr. Sarah Smith today, discussed Product X"})

    # Assertions
    assert "✅" in result or "Interaction logged" in result
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.close.called


@patch("app.agents.tools.SessionLocal")
@patch("app.agents.tools.PRIMARY_LLM")
def test_log_interaction_llm_error(mock_llm, mock_session_cls):
    """Test that log_interaction handles LLM errors gracefully."""
    from app.agents.tools import log_interaction

    # Mock LLM to return invalid JSON
    mock_llm.invoke.return_value = _make_llm_response("Error: cannot parse")

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db

    result = log_interaction.invoke({"note": "Met Dr. Smith"})

    # Should return an error message, not crash
    assert "❌" in result or "Error" in result
    assert mock_db.close.called


# ═══════════════════════════════════════════════════════════════
# TOOL 2 — edit_interaction
# ═══════════════════════════════════════════════════════════════

@patch("app.agents.tools.SessionLocal")
@patch("app.agents.tools.PRIMARY_LLM")
def test_edit_interaction_success(mock_llm, mock_session_cls):
    """Test that edit_interaction updates the correct fields."""
    from app.agents.tools import edit_interaction

    # Mock existing interaction
    mock_interaction = _make_mock_interaction(sentiment="neutral")
    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_interaction

    # Mock LLM to return update fields
    update_json = {"sentiment": "positive", "outcomes": "Agreed to trial"}
    mock_llm.invoke.return_value = _make_llm_response(json.dumps(update_json))

    interaction_id = str(mock_interaction.id)
    result = edit_interaction.invoke({
        "interaction_id": interaction_id,
        "edit_request": "Change sentiment to positive and update outcomes",
    })

    # Assertions
    assert "✅" in result or "updated" in result.lower()
    assert mock_db.commit.called
    assert mock_db.close.called


@patch("app.agents.tools.SessionLocal")
def test_edit_interaction_not_found(mock_session_cls):
    """Test that edit_interaction handles missing interaction."""
    from app.agents.tools import edit_interaction

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = edit_interaction.invoke({
        "interaction_id": str(uuid.uuid4()),
        "edit_request": "Change sentiment to positive",
    })

    assert "not found" in result.lower() or "❌" in result
    assert mock_db.close.called


# ═══════════════════════════════════════════════════════════════
# TOOL 3 — get_hcp_history
# ═══════════════════════════════════════════════════════════════

@patch("app.agents.tools.SessionLocal")
@patch("app.agents.tools.CONTEXT_LLM")
def test_get_hcp_history_success(mock_llm, mock_session_cls):
    """Test that get_hcp_history retrieves and summarises history."""
    from app.agents.tools import get_hcp_history

    mock_hcp = _make_mock_hcp()
    mock_interaction = _make_mock_interaction(hcp_id=mock_hcp.id)

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    # First query: find HCP by name
    mock_db.query.return_value.filter.return_value.first.return_value = mock_hcp
    # Second query: get interactions
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        mock_interaction
    ]

    # Mock LLM summary
    mock_llm.invoke.return_value = _make_llm_response(
        "Dr. Smith has been engaged with positive sentiment across 1 visit."
    )

    result = get_hcp_history.invoke({"hcp_identifier": "Smith"})

    assert "History" in result or "📋" in result
    assert mock_llm.invoke.called
    assert mock_db.close.called


@patch("app.agents.tools.SessionLocal")
def test_get_hcp_history_not_found(mock_session_cls):
    """Test that get_hcp_history handles unknown HCP."""
    from app.agents.tools import get_hcp_history

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = get_hcp_history.invoke({"hcp_identifier": "NonexistentDoctor"})

    assert "No HCP found" in result or "❌" in result
    assert mock_db.close.called


# ═══════════════════════════════════════════════════════════════
# TOOL 4 — suggest_follow_up
# ═══════════════════════════════════════════════════════════════

@patch("app.agents.tools.SessionLocal")
@patch("app.agents.tools.CONTEXT_LLM")
def test_suggest_follow_up_success(mock_llm, mock_session_cls):
    """Test that suggest_follow_up generates and saves suggestions."""
    from app.agents.tools import suggest_follow_up

    mock_hcp = _make_mock_hcp()
    mock_interaction = _make_mock_interaction(hcp_id=mock_hcp.id)

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db

    # Mock queries: find interaction, find HCP, find materials, find samples
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_interaction,  # find interaction
        mock_hcp,          # find HCP
    ]
    mock_db.query.return_value.filter.return_value.all.side_effect = [
        [],  # materials
        [],  # samples
    ]

    # Mock LLM to return suggestion array
    suggestions = [
        "Schedule follow-up visit in 2 weeks to discuss trial results",
        "Send Phase III clinical study PDF via email",
        "Prepare samples of Product Y for next visit",
    ]
    mock_llm.invoke.return_value = _make_llm_response(json.dumps(suggestions))

    result = suggest_follow_up.invoke({"interaction_id": str(mock_interaction.id)})

    assert "💡" in result or "Follow-up" in result
    assert "Saved" in result or mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.close.called


@patch("app.agents.tools.SessionLocal")
def test_suggest_follow_up_not_found(mock_session_cls):
    """Test that suggest_follow_up handles missing interaction."""
    from app.agents.tools import suggest_follow_up

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = suggest_follow_up.invoke({"interaction_id": str(uuid.uuid4())})

    assert "not found" in result.lower() or "❌" in result
    assert mock_db.close.called


# ═══════════════════════════════════════════════════════════════
# TOOL 5 — search_hcp
# ═══════════════════════════════════════════════════════════════

@patch("app.agents.tools.SessionLocal")
def test_search_hcp_found(mock_session_cls):
    """Test that search_hcp returns matching HCPs."""
    from app.agents.tools import search_hcp

    mock_hcp1 = _make_mock_hcp("Dr. Sarah Smith", "Cardiology")
    mock_hcp2 = _make_mock_hcp("Dr. John Smith", "Neurology")

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
        mock_hcp1, mock_hcp2
    ]

    result = search_hcp.invoke({"query": "Smith"})

    assert "Found 2" in result or "🔍" in result
    assert "Smith" in result
    assert mock_db.close.called


@patch("app.agents.tools.SessionLocal")
def test_search_hcp_not_found(mock_session_cls):
    """Test that search_hcp handles no results."""
    from app.agents.tools import search_hcp

    mock_db = MagicMock()
    mock_session_cls.return_value = mock_db
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    result = search_hcp.invoke({"query": "NonexistentDoctor"})

    assert "No HCPs found" in result or "🔍" in result
    assert mock_db.close.called


# ═══════════════════════════════════════════════════════════════
# Integration — ALL_TOOLS list
# ═══════════════════════════════════════════════════════════════

def test_all_tools_count():
    """Verify that exactly 5 tools are registered."""
    from app.agents.tools import ALL_TOOLS

    assert len(ALL_TOOLS) == 5, f"Expected 5 tools, got {len(ALL_TOOLS)}"


def test_all_tools_names():
    """Verify that the correct 5 tools are registered."""
    from app.agents.tools import ALL_TOOLS

    tool_names = {t.name for t in ALL_TOOLS}
    expected = {
        "log_interaction",
        "edit_interaction",
        "get_hcp_history",
        "suggest_follow_up",
        "search_hcp",
    }
    assert tool_names == expected, f"Tool names mismatch: {tool_names} != {expected}"
