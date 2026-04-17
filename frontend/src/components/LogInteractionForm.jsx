/**
 * Log Interaction Form — Structured Form UI
 *
 * Displays all fields required to log an HCP interaction:
 *   - HCP Name (search/select)
 *   - Interaction Type (dropdown)
 *   - Date & Time (pickers)
 *   - Attendees (multi-input tags)
 *   - Topics Discussed (textarea)
 *   - Voice Note Summarize (consent-gated button)
 *   - Materials Shared (search/add)
 *   - Samples Distributed (add)
 *   - Sentiment (radio buttons)
 *   - Outcomes (textarea)
 *   - Follow-up Actions (textarea)
 *   - AI Suggested Follow-ups (read-only display)
 *
 * All state managed by Redux — no local useState for form fields.
 */

import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  updateFormField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
  addSample,
  removeSample,
  resetForm,
  submitInteraction,
  fetchFollowUps,
} from "../features/interactionSlice";
import { searchHCPs } from "../api/api";
import "./LogInteractionForm.css";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference", "Virtual"];
const MATERIAL_TYPES = [
  "Brochure",
  "Clinical Study",
  "Presentation",
  "Product Info",
  "Sample Card",
  "Other",
];

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const form = useSelector((state) => state.interaction.form);
  const submitStatus = useSelector((state) => state.interaction.submitStatus);
  const error = useSelector((state) => state.interaction.error);
  const successMessage = useSelector((state) => state.interaction.successMessage);
  const lastInteractionId = useSelector((state) => state.interaction.lastInteractionId);
  const aiFollowUps = useSelector((state) => state.interaction.aiFollowUps);
  const followUpStatus = useSelector((state) => state.interaction.followUpStatus);

  // Local state for HCP search dropdown and material/sample inputs
  const [hcpSearchResults, setHcpSearchResults] = useState([]);
  const [showHcpDropdown, setShowHcpDropdown] = useState(false);
  const [newAttendee, setNewAttendee] = useState("");
  const [newMaterial, setNewMaterial] = useState({ name: "", type: "Brochure" });
  const [newSample, setNewSample] = useState({ name: "", quantity: 1 });
  const [showVoiceNoteConsent, setShowVoiceNoteConsent] = useState(false);

  // ── HCP Search ──────────────────────────────────────────
  const handleHcpSearch = async (e) => {
    const query = e.target.value;
    dispatch(updateFormField({ field: "hcpName", value: query }));
    setShowHcpDropdown(true);

    if (query.length > 2) {
      try {
        const res = await searchHCPs(query);
        // Mock parsing — adjust based on actual API response
        const results = res.data?.data?.split("\n") || [];
        setHcpSearchResults(results.filter((r) => r.trim()));
      } catch (err) {
        setHcpSearchResults([]);
      }
    } else {
      setHcpSearchResults([]);
    }
  };

  const selectHcp = (hcpName) => {
    dispatch(updateFormField({ field: "hcpName", value: hcpName }));
    setShowHcpDropdown(false);
    setHcpSearchResults([]);
  };

  // ── Attendees ───────────────────────────────────────────
  const handleAddAttendee = () => {
    if (newAttendee.trim()) {
      dispatch(addAttendee(newAttendee.trim()));
      setNewAttendee("");
    }
  };

  const handleRemoveAttendee = (attendee) => {
    dispatch(removeAttendee(attendee));
  };

  // ── Materials ───────────────────────────────────────────
  const handleAddMaterial = () => {
    if (newMaterial.name.trim()) {
      dispatch(addMaterial({ name: newMaterial.name, type: newMaterial.type }));
      setNewMaterial({ name: "", type: "Brochure" });
    }
  };

  const handleRemoveMaterial = (index) => {
    dispatch(removeMaterial(index));
  };

  // ── Samples ─────────────────────────────────────────────
  const handleAddSample = () => {
    if (newSample.name.trim() && newSample.quantity > 0) {
      dispatch(addSample({ name: newSample.name, quantity: parseInt(newSample.quantity) }));
      setNewSample({ name: "", quantity: 1 });
    }
  };

  const handleRemoveSample = (index) => {
    dispatch(removeSample(index));
  };

  // ── Form Submit ─────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Build the note for the LLM
    const note = `
HCP: ${form.hcpName}
Interaction Type: ${form.interactionType}
Date: ${form.date} ${form.time || ""}
Attendees: ${form.attendees.join(", ") || "None"}
Topics Discussed: ${form.topicsDiscussed}
Materials Shared: ${form.materialsShared.map((m) => `${m.name} (${m.type})`).join(", ") || "None"}
Samples Distributed: ${form.samplesDistributed.map((s) => `${s.name} x${s.quantity}`).join(", ") || "None"}
Observed Sentiment: ${form.sentiment}
Outcomes: ${form.outcomes}
Follow-up Actions: ${form.followUpActions}
    `.trim();

    dispatch(submitInteraction(note));
  };

  // ── Generate Follow-ups ─────────────────────────────────
  const handleGenerateFollowups = () => {
    if (lastInteractionId) {
      dispatch(fetchFollowUps(lastInteractionId));
    }
  };

  return (
    <div className="log-interaction-form">
      <div className="form-container">
        <h1 className="form-title">Log HCP Interaction</h1>

        {/* Success / Error Messages */}
        {successMessage && (
          <div className="alert alert-success">
            ✅ {successMessage}
          </div>
        )}
        {error && (
          <div className="alert alert-error">
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form">
          {/* ──────────────────────────────────────────── */}
          {/* Section 1: HCP & Interaction Type */}
          {/* ──────────────────────────────────────────── */}
          <section className="form-section">
            <h2 className="section-title">Interaction Details</h2>

            {/* HCP Name Search/Select */}
            <div className="form-group">
              <label htmlFor="hcp-name" className="form-label">
                HCP Name *
              </label>
              <div className="relative">
                <input
                  id="hcp-name"
                  type="text"
                  value={form.hcpName}
                  onChange={handleHcpSearch}
                  onFocus={() => setShowHcpDropdown(true)}
                  placeholder="Search HCP by name (Dr. Smith, etc.)"
                  className="form-input"
                  required
                />
                {showHcpDropdown && hcpSearchResults.length > 0 && (
                  <div className="dropdown-menu">
                    {hcpSearchResults.slice(0, 5).map((result, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => selectHcp(result.trim())}
                        className="dropdown-item"
                      >
                        {result.trim()}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Interaction Type */}
            <div className="form-group">
              <label htmlFor="interaction-type" className="form-label">
                Interaction Type *
              </label>
              <select
                id="interaction-type"
                value={form.interactionType}
                onChange={(e) =>
                  dispatch(updateFormField({ field: "interactionType", value: e.target.value }))
                }
                className="form-input"
                required
              >
                {INTERACTION_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </section>

          {/* ──────────────────────────────────────────── */}
          {/* Section 2: Date, Time & Attendees */}
          {/* ──────────────────────────────────────────── */}
          <section className="form-section">
            <h2 className="section-title">Date & Attendees</h2>

            {/* Date & Time Row */}
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="date" className="form-label">
                  Date *
                </label>
                <input
                  id="date"
                  type="date"
                  value={form.date}
                  onChange={(e) =>
                    dispatch(updateFormField({ field: "date", value: e.target.value }))
                  }
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="time" className="form-label">
                  Time
                </label>
                <input
                  id="time"
                  type="time"
                  value={form.time}
                  onChange={(e) =>
                    dispatch(updateFormField({ field: "time", value: e.target.value }))
                  }
                  className="form-input"
                />
              </div>
            </div>

            {/* Attendees Multi-input */}
            <div className="form-group">
              <label htmlFor="attendees-input" className="form-label">
                Attendees
              </label>
              <div className="multi-input-container">
                <div className="multi-input-field">
                  <input
                    id="attendees-input"
                    type="text"
                    value={newAttendee}
                    onChange={(e) => setNewAttendee(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddAttendee();
                      }
                    }}
                    placeholder="Enter attendee name and press Enter"
                    className="form-input"
                  />
                  <button
                    type="button"
                    onClick={handleAddAttendee}
                    className="btn btn-secondary btn-sm"
                  >
                    Add
                  </button>
                </div>
                <div className="tags-container">
                  {form.attendees.map((attendee) => (
                    <div key={attendee} className="tag">
                      {attendee}
                      <button
                        type="button"
                        onClick={() => handleRemoveAttendee(attendee)}
                        className="tag-remove"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* ──────────────────────────────────────────── */}
          {/* Section 3: Topics & Voice Note */}
          {/* ──────────────────────────────────────────── */}
          <section className="form-section">
            <h2 className="section-title">Topics & Notes</h2>

            {/* Topics Discussed */}
            <div className="form-group">
              <label htmlFor="topics" className="form-label">
                Topics Discussed *
              </label>
              <textarea
                id="topics"
                value={form.topicsDiscussed}
                onChange={(e) =>
                  dispatch(updateFormField({ field: "topicsDiscussed", value: e.target.value }))
                }
                placeholder="Summarize the topics discussed during this interaction..."
                rows={4}
                className="form-textarea"
                required
              />
            </div>

            {/* Voice Note Summarize Button (Consent-gated) */}
            <div className="form-group">
              <button
                type="button"
                onClick={() => setShowVoiceNoteConsent(true)}
                className="btn btn-outline"
              >
                🎤 Summarize from Voice Note (Requires Consent)
              </button>
              {showVoiceNoteConsent && (
                <div className="consent-modal">
                  <div className="consent-content">
                    <p>
                      This feature will record or upload a voice note and transcribe it to
                      summarize the interaction. Your consent is required.
                    </p>
                    <div className="consent-actions">
                      <button
                        type="button"
                        onClick={() => setShowVoiceNoteConsent(false)}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                      <button type="button" className="btn btn-primary" disabled>
                        Accept & Record (Coming Soon)
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* ──────────────────────────────────────────── */}
          {/* Section 4: Materials & Samples */}
          {/* ──────────────────────────────────────────── */}
          <section className="form-section">
            <h2 className="section-title">Materials & Samples</h2>

            {/* Materials Shared */}
            <div className="form-group">
              <label className="form-label">Materials Shared</label>
              <div className="multi-item-container">
                <div className="multi-item-input">
                  <input
                    type="text"
                    value={newMaterial.name}
                    onChange={(e) =>
                      setNewMaterial({ ...newMaterial, name: e.target.value })
                    }
                    placeholder="Material name"
                    className="form-input"
                  />
                  <select
                    value={newMaterial.type}
                    onChange={(e) =>
                      setNewMaterial({ ...newMaterial, type: e.target.value })
                    }
                    className="form-input form-input-sm"
                  >
                    {MATERIAL_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleAddMaterial}
                    className="btn btn-secondary btn-sm"
                  >
                    Add Material
                  </button>
                </div>
                <div className="items-list">
                  {form.materialsShared.map((material, idx) => (
                    <div key={idx} className="item-row">
                      <span className="item-text">
                        {material.name} ({material.type})
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveMaterial(idx)}
                        className="btn-remove"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Samples Distributed */}
            <div className="form-group">
              <label className="form-label">Samples Distributed</label>
              <div className="multi-item-container">
                <div className="multi-item-input">
                  <input
                    type="text"
                    value={newSample.name}
                    onChange={(e) => setNewSample({ ...newSample, name: e.target.value })}
                    placeholder="Sample name"
                    className="form-input"
                  />
                  <input
                    type="number"
                    min="1"
                    value={newSample.quantity}
                    onChange={(e) =>
                      setNewSample({ ...newSample, quantity: e.target.value })
                    }
                    placeholder="Qty"
                    className="form-input form-input-sm"
                  />
                  <button
                    type="button"
                    onClick={handleAddSample}
                    className="btn btn-secondary btn-sm"
                  >
                    Add Sample
                  </button>
                </div>
                <div className="items-list">
                  {form.samplesDistributed.map((sample, idx) => (
                    <div key={idx} className="item-row">
                      <span className="item-text">
                        {sample.name} × {sample.quantity}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveSample(idx)}
                        className="btn-remove"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* ──────────────────────────────────────────── */}
          {/* Section 5: Sentiment, Outcomes & Follow-ups */}
          {/* ──────────────────────────────────────────── */}
          <section className="form-section">
            <h2 className="section-title">Sentiment & Outcomes</h2>

            {/* Observed Sentiment (Radio) */}
            <div className="form-group">
              <label className="form-label">Observed/Inferred HCP Sentiment *</label>
              <div className="radio-group">
                {["Positive", "Neutral", "Negative"].map((sentiment) => (
                  <label key={sentiment} className="radio-label">
                    <input
                      type="radio"
                      name="sentiment"
                      value={sentiment}
                      checked={form.sentiment === sentiment}
                      onChange={(e) =>
                        dispatch(updateFormField({ field: "sentiment", value: e.target.value }))
                      }
                      required
                    />
                    <span className="radio-text">{sentiment}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Outcomes */}
            <div className="form-group">
              <label htmlFor="outcomes" className="form-label">
                Outcomes
              </label>
              <textarea
                id="outcomes"
                value={form.outcomes}
                onChange={(e) =>
                  dispatch(updateFormField({ field: "outcomes", value: e.target.value }))
                }
                placeholder="What were the outcomes or decisions from this interaction?"
                rows={3}
                className="form-textarea"
              />
            </div>

            {/* Follow-up Actions */}
            <div className="form-group">
              <label htmlFor="followup-actions" className="form-label">
                Follow-up Actions
              </label>
              <textarea
                id="followup-actions"
                value={form.followUpActions}
                onChange={(e) =>
                  dispatch(updateFormField({ field: "followUpActions", value: e.target.value }))
                }
                placeholder="What follow-up actions need to be taken?"
                rows={3}
                className="form-textarea"
              />
            </div>
          </section>

          {/* ──────────────────────────────────────────── */}
          {/* Form Actions */}
          {/* ──────────────────────────────────────────── */}
          <div className="form-actions">
            <button
              type="button"
              onClick={() => dispatch(resetForm())}
              className="btn btn-secondary"
            >
              Reset
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitStatus === "loading"}
            >
              {submitStatus === "loading" ? "Submitting..." : "Submit Interaction"}
            </button>
          </div>
        </form>

        {/* ──────────────────────────────────────────── */}
        {/* AI Suggested Follow-ups Section */}
        {/* ──────────────────────────────────────────── */}
        {lastInteractionId && (
          <section className="followups-section">
            <div className="followups-header">
              <h2 className="section-title">AI Suggested Follow-ups</h2>
              <button
                type="button"
                onClick={handleGenerateFollowups}
                className="btn btn-primary btn-sm"
                disabled={followUpStatus === "loading"}
              >
                {followUpStatus === "loading" ? "Generating..." : "Generate Suggestions"}
              </button>
            </div>

            {aiFollowUps.length > 0 && (
              <div className="followups-list">
                {aiFollowUps.map((suggestion, idx) => (
                  <div key={idx} className="followup-item">
                    <span className="followup-number">{idx + 1}</span>
                    <p className="followup-text">{suggestion}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
