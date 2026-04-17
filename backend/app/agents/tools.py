"""
LangChain Tool Definitions — HCP Interaction Logger

Five tools that the LangGraph agent can invoke:
  1. log_interaction    — Parse & save a new interaction
  2. edit_interaction   — Update an existing interaction
  3. get_hcp_history    — Retrieve & summarise HCP history
  4. suggest_follow_up  — Generate AI follow-up suggestions
  5. search_hcp         — Search HCPs by name / specialty

Each tool uses the Groq LLM (via ChatGroq) for NLP tasks
and SQLAlchemy for database operations.
"""

import json
import os
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.db.models import (
    HCP,
    Interaction,
    MaterialShared,
    SampleDistributed,
    FollowUpSuggestion,
)
from app.agents.prompts import (
    EXTRACT_INTERACTION_PROMPT,
    EDIT_INTERACTION_PROMPT,
    SUMMARISE_HISTORY_PROMPT,
    SUGGEST_FOLLOW_UP_PROMPT,
)

load_dotenv()

# ── LLM Instances ──────────────────────────────────────────
# Primary model for fast, lightweight tasks (extraction, search)
PRIMARY_LLM = ChatGroq(
    model="gemma2-9b-it",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,        # low temperature for structured output
    max_tokens=2048,
)

# Fallback / context-heavy model for summarisation and generation
CONTEXT_LLM = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,        # slightly creative for suggestions
    max_tokens=4096,
)


def _get_db():
    """Create a scoped database session for use within a tool."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def _parse_json(text: str) -> dict | list:
    """Extract and parse JSON from LLM output, stripping markdown fences."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


# ═══════════════════════════════════════════════════════════════
# TOOL 1 — log_interaction
# ═══════════════════════════════════════════════════════════════

@tool
def log_interaction(note: str) -> str:
    """Log a new HCP interaction from a field rep's natural language note.

    Takes the raw text describing a meeting/call (e.g. 'Met Dr. Smith today,
    discussed Product X efficacy, positive sentiment, shared brochure') and
    uses the LLM to extract structured entities, then saves everything to
    the database.

    Args:
        note: Free-text note from the field rep describing the interaction.

    Returns:
        Confirmation message with the saved interaction details.
    """
    db = _get_db()
    try:
        # ── Step 1: Use LLM to extract structured entities from raw text ──
        today_str = date.today().isoformat()
        prompt = EXTRACT_INTERACTION_PROMPT.format(note=note, today=today_str)
        response = PRIMARY_LLM.invoke(prompt)
        extracted = _parse_json(response.content)

        # ── Step 2: Find or create the HCP record ──
        hcp_name = extracted.get("hcp_name", "Unknown HCP")
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()

        if not hcp:
            # Create a new HCP profile with extracted info
            hcp = HCP(
                name=hcp_name,
                specialty=extracted.get("specialty") or "General",
                location=extracted.get("location"),
                hospital=extracted.get("hospital"),
            )
            db.add(hcp)
            db.flush()  # get the HCP id without committing

        # ── Step 3: Create the interaction record ──
        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=extracted.get("interaction_type", "in-person"),
            date=extracted.get("date", today_str),
            time=extracted.get("time"),
            attendees=extracted.get("attendees"),
            topics_discussed=extracted.get("topics_discussed"),
            outcomes=extracted.get("outcomes"),
            follow_up_actions=extracted.get("follow_up_actions"),
            sentiment=extracted.get("sentiment", "neutral"),
        )
        db.add(interaction)
        db.flush()

        # ── Step 4: Save materials shared (if any) ──
        materials = extracted.get("materials_shared") or []
        for mat in materials:
            if mat.get("material_name"):
                db.add(MaterialShared(
                    interaction_id=interaction.id,
                    material_name=mat["material_name"],
                    material_type=mat.get("material_type", "other"),
                ))

        # ── Step 5: Save samples distributed (if any) ──
        samples = extracted.get("samples_distributed") or []
        for samp in samples:
            if samp.get("sample_name"):
                db.add(SampleDistributed(
                    interaction_id=interaction.id,
                    sample_name=samp["sample_name"],
                    quantity=samp.get("quantity", 1),
                ))

        db.commit()

        # ── Step 6: Return confirmation ──
        return (
            f"✅ Interaction logged successfully!\n"
            f"• ID: {interaction.id}\n"
            f"• HCP: {hcp.name} ({hcp.specialty})\n"
            f"• Type: {interaction.interaction_type}\n"
            f"• Date: {interaction.date}\n"
            f"• Sentiment: {interaction.sentiment}\n"
            f"• Topics: {interaction.topics_discussed}\n"
            f"• Materials shared: {len(materials)}\n"
            f"• Samples given: {len(samples)}"
        )

    except Exception as e:
        db.rollback()
        return f"❌ Error logging interaction: {str(e)}"
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TOOL 2 — edit_interaction
# ═══════════════════════════════════════════════════════════════

@tool
def edit_interaction(interaction_id: str, edit_request: str) -> str:
    """Edit an existing interaction record based on a natural language request.

    The LLM interprets the change request, maps it to database fields,
    and applies the update.

    Args:
        interaction_id: UUID of the interaction to edit.
        edit_request: Natural language description of changes
                      (e.g. 'change sentiment to positive').

    Returns:
        Confirmation with the updated fields.
    """
    db = _get_db()
    try:
        # ── Step 1: Fetch the existing interaction ──
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id
        ).first()

        if not interaction:
            return f"❌ Interaction with ID {interaction_id} not found."

        # ── Step 2: Build current record summary for the LLM ──
        current_record = (
            f"interaction_type: {interaction.interaction_type}\n"
            f"date: {interaction.date}\n"
            f"time: {interaction.time}\n"
            f"attendees: {interaction.attendees}\n"
            f"topics_discussed: {interaction.topics_discussed}\n"
            f"outcomes: {interaction.outcomes}\n"
            f"follow_up_actions: {interaction.follow_up_actions}\n"
            f"sentiment: {interaction.sentiment}"
        )

        # ── Step 3: Use LLM to interpret the edit request ──
        prompt = EDIT_INTERACTION_PROMPT.format(
            current_record=current_record,
            edit_request=edit_request,
        )
        response = PRIMARY_LLM.invoke(prompt)
        updates = _parse_json(response.content)

        # ── Step 4: Validate and apply updates ──
        updatable_fields = {
            "interaction_type", "date", "time", "attendees",
            "topics_discussed", "outcomes", "follow_up_actions", "sentiment",
        }

        applied = {}
        for field, value in updates.items():
            if field in updatable_fields:
                setattr(interaction, field, value)
                applied[field] = value

        if not applied:
            return "⚠️ No valid fields to update were found in your request."

        db.commit()

        # ── Step 5: Return confirmation ──
        changes_str = "\n".join(f"  • {k}: {v}" for k, v in applied.items())
        return (
            f"✅ Interaction {interaction_id} updated!\n"
            f"Changed fields:\n{changes_str}"
        )

    except Exception as e:
        db.rollback()
        return f"❌ Error editing interaction: {str(e)}"
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TOOL 3 — get_hcp_history
# ═══════════════════════════════════════════════════════════════

@tool
def get_hcp_history(hcp_identifier: str, limit: int = 10) -> str:
    """Retrieve and summarise the interaction history for a specific HCP.

    Searches by name (partial match) or UUID. Returns the last N
    interactions summarised by the LLM.

    Args:
        hcp_identifier: HCP name (partial match) or UUID.
        limit: Maximum number of interactions to retrieve (default 10).

    Returns:
        LLM-generated summary of the HCP's interaction history.
    """
    db = _get_db()
    try:
        # ── Step 1: Find the HCP ──
        # Try UUID first, fall back to name search
        hcp = None
        try:
            uuid_val = UUID(hcp_identifier)
            hcp = db.query(HCP).filter(HCP.id == uuid_val).first()
        except (ValueError, AttributeError):
            hcp = db.query(HCP).filter(
                HCP.name.ilike(f"%{hcp_identifier}%")
            ).first()

        if not hcp:
            return f"❌ No HCP found matching '{hcp_identifier}'."

        # ── Step 2: Fetch interactions ordered by date (most recent first) ──
        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.date.desc())
            .limit(limit)
            .all()
        )

        if not interactions:
            return f"📋 No interactions found for {hcp.name}."

        # ── Step 3: Serialize interactions for the LLM ──
        interactions_data = []
        for ix in interactions:
            interactions_data.append({
                "id": str(ix.id),
                "type": ix.interaction_type,
                "date": str(ix.date),
                "topics": ix.topics_discussed,
                "outcomes": ix.outcomes,
                "sentiment": ix.sentiment,
                "follow_up": ix.follow_up_actions,
            })

        # ── Step 4: Use context LLM to generate a rich summary ──
        prompt = SUMMARISE_HISTORY_PROMPT.format(
            hcp_name=hcp.name,
            interactions_json=json.dumps(interactions_data, indent=2),
        )
        response = CONTEXT_LLM.invoke(prompt)

        return (
            f"📋 History for {hcp.name} ({hcp.specialty}) — "
            f"{len(interactions)} interaction(s):\n\n"
            f"{response.content}"
        )

    except Exception as e:
        return f"❌ Error retrieving history: {str(e)}"
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TOOL 4 — suggest_follow_up
# ═══════════════════════════════════════════════════════════════

@tool
def suggest_follow_up(interaction_id: str) -> str:
    """Generate AI-powered follow-up suggestions for a specific interaction.

    Analyses the interaction context and generates 2-3 actionable
    follow-up items, saving them to the follow_up_suggestions table.

    Args:
        interaction_id: UUID of the interaction to generate suggestions for.

    Returns:
        The generated follow-up suggestions.
    """
    db = _get_db()
    try:
        # ── Step 1: Load the interaction with related data ──
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id
        ).first()

        if not interaction:
            return f"❌ Interaction {interaction_id} not found."

        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()

        # Gather materials and samples for context
        materials = db.query(MaterialShared).filter(
            MaterialShared.interaction_id == interaction.id
        ).all()
        samples = db.query(SampleDistributed).filter(
            SampleDistributed.interaction_id == interaction.id
        ).all()

        materials_str = ", ".join(
            f"{m.material_name} ({m.material_type})" for m in materials
        ) or "None"
        samples_str = ", ".join(
            f"{s.sample_name} x{s.quantity}" for s in samples
        ) or "None"

        # ── Step 2: Use context LLM to generate follow-up suggestions ──
        prompt = SUGGEST_FOLLOW_UP_PROMPT.format(
            hcp_name=hcp.name if hcp else "Unknown",
            specialty=hcp.specialty if hcp else "Unknown",
            interaction_type=interaction.interaction_type,
            date=str(interaction.date),
            topics_discussed=interaction.topics_discussed or "Not recorded",
            outcomes=interaction.outcomes or "Not recorded",
            sentiment=interaction.sentiment or "neutral",
            materials=materials_str,
            samples=samples_str,
        )
        response = CONTEXT_LLM.invoke(prompt)
        suggestions = _parse_json(response.content)

        # ── Step 3: Save suggestions to the database ──
        saved_suggestions = []
        for suggestion_text in suggestions:
            suggestion = FollowUpSuggestion(
                interaction_id=interaction.id,
                suggestion_text=suggestion_text,
                generated_by_ai=True,
            )
            db.add(suggestion)
            saved_suggestions.append(suggestion_text)

        db.commit()

        # ── Step 4: Return formatted suggestions ──
        suggestions_str = "\n".join(
            f"  {i+1}. {s}" for i, s in enumerate(saved_suggestions)
        )
        return (
            f"💡 Follow-up suggestions for interaction {interaction_id}:\n"
            f"{suggestions_str}\n\n"
            f"(Saved {len(saved_suggestions)} suggestions to database)"
        )

    except Exception as e:
        db.rollback()
        return f"❌ Error generating suggestions: {str(e)}"
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TOOL 5 — search_hcp
# ═══════════════════════════════════════════════════════════════

@tool
def search_hcp(query: str) -> str:
    """Search for Healthcare Professionals by name or specialty.

    Performs a case-insensitive partial match against both
    the name and specialty fields.

    Args:
        query: Partial name or specialty to search for
               (e.g. 'Smith' or 'Cardiology').

    Returns:
        List of matching HCP records.
    """
    db = _get_db()
    try:
        # ── Query with ILIKE for case-insensitive partial matching ──
        results = db.query(HCP).filter(
            or_(
                HCP.name.ilike(f"%{query}%"),
                HCP.specialty.ilike(f"%{query}%"),
            )
        ).limit(20).all()

        if not results:
            return f"🔍 No HCPs found matching '{query}'."

        # ── Format results ──
        lines = []
        for hcp in results:
            lines.append(
                f"• {hcp.name} | {hcp.specialty} | "
                f"{hcp.hospital or 'N/A'} | {hcp.location or 'N/A'} | "
                f"ID: {hcp.id}"
            )

        return (
            f"🔍 Found {len(results)} HCP(s) matching '{query}':\n"
            + "\n".join(lines)
        )

    except Exception as e:
        return f"❌ Error searching HCPs: {str(e)}"
    finally:
        db.close()


# ── Export all tools as a list for the graph ────────────────

ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    get_hcp_history,
    suggest_follow_up,
    search_hcp,
]
