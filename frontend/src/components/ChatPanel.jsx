/**
 * ChatPanel — Right-side AI assistant chat interface.
 *
 * Displays conversation history with ability to:
 *   1. Log interactions via natural language (sends to POST /interactions/log)
 *   2. Display extracted interaction data and follow-up suggestions
 *   3. Maintain separate state from the form (LogInteractionForm)
 */

import { useState, useRef, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  sendMessage,
  addUserMessage,
  clearChat,
} from "../features/chatSlice";
import "./ChatPanel.css";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, status, lastInteractionId } = useSelector((state) => state.chat);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send message through the full LangGraph agent (POST /api/chat) ──
  const handleLogInteraction = () => {
    const trimmed = input.trim();
    if (!trimmed || status === "loading") return;

    // Add user message to chat history
    dispatch(addUserMessage(trimmed));
    // Send through full LangGraph agent — the agent autonomously
    // decides which tool(s) to invoke based on the message content
    dispatch(sendMessage(trimmed));
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleLogInteraction();
    }
  };

  // Parse and format interaction response
  const parseInteractionResponse = (responseText) => {
    if (!responseText) return null;

    // Extract fields from the response (e.g., "ID: UUID", "HCP: Name", etc.)
    const fields = {};
    const lines = responseText.split("\n");

    lines.forEach((line) => {
      const match = line.match(/^•\s*([^:]+):\s*(.+)$/);
      if (match) {
        fields[match[1].trim()] = match[2].trim();
      }
    });

    return Object.keys(fields).length > 0 ? fields : null;
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-avatar">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2a5 5 0 0 1 5 5v3a5 5 0 0 1-10 0V7a5 5 0 0 1 5-5Z" />
              <path d="M17 10c3 0 5 1.5 5 4v2H2v-2c0-2.5 2-4 5-4" />
            </svg>
          </div>
          <div>
            <h3>AI Assistant</h3>
            <span className="chat-status-dot">
              <span className={`dot ${status === "loading" ? "pulsing" : ""}`}></span>
              {status === "loading" ? "Analyzing..." : "Ready"}
            </span>
          </div>
        </div>
        <button
          className="chat-clear-btn"
          onClick={() => dispatch(clearChat())}
          title="Clear chat"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">📝</div>
            <p>Describe an interaction in natural language and I'll extract the details for you.</p>
            <div className="chat-examples">
              <span
                className="example-chip"
                onClick={() =>
                  setInput(
                    "Met Dr. Patel today in her clinic, discussed Metformin efficacy, shared a clinical study, positive sentiment"
                  )
                }
              >
                "Met Dr. Patel today..."
              </span>
              <span
                className="example-chip"
                onClick={() =>
                  setInput(
                    "Virtual call with Dr. Smith via Zoom, discussed Product X, they seemed interested, gave samples"
                  )
                }
              >
                "Virtual call with Dr. Smith..."
              </span>
              <span
                className="example-chip"
                onClick={() =>
                  setInput("Email to Dr. Johnson about Phase III results, neutral response")
                }
              >
                "Email to Dr. Johnson..."
              </span>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.role}`}>
            {msg.role === "assistant" && <div className="bubble-avatar">AI</div>}
            <div className="bubble-content">
              {/* Display plain text response */}
              <div className="bubble-text">{msg.content}</div>

              {/* If this is an interaction log response, show extracted fields */}
              {msg.type === "interaction_log" && (
                <div className="interaction-summary">
                  <div className="summary-title">✓ Interaction Logged</div>
                  {parseInteractionResponse(msg.content) && (
                    <div className="summary-fields">
                      {Object.entries(parseInteractionResponse(msg.content)).map(
                        ([key, value]) => (
                          <div key={key} className="summary-field">
                            <span className="field-key">{key}:</span>
                            <span className="field-value">{value}</span>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {status === "loading" && (
          <div className="chat-bubble assistant">
            <div className="bubble-avatar">AI</div>
            <div className="bubble-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Follow-ups Section (shown when interaction is logged) */}
      {lastInteractionId && (
        <div className="chat-followups-section">
          <div className="followups-label">💡 AI Suggested Follow-ups</div>
          <p className="followups-hint">
            Use the "Generate Suggestions" button in the right panel to get AI-powered
            follow-up actions.
          </p>
        </div>
      )}

      {/* Input Area */}
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="E.g., Met Dr. Smith today to discuss Product X efficacy. Shared brochure. Positive sentiment."
          rows={1}
          disabled={status === "loading"}
        />
        <button
          className="chat-send-btn"
          onClick={handleLogInteraction}
          disabled={!input.trim() || status === "loading"}
        >
          {status === "loading" ? "..." : "Log"}
        </button>
      </div>
    </div>
  );
}
