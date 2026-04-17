import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage, logInteraction } from "../api/api";

// ── Async Thunks ──────────────────────────────────────────

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async (message, { rejectWithValue }) => {
    try {
      const res = await sendChatMessage(message);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

// Log interaction via chat (sends natural language note to backend)
export const logInteractionFromChat = createAsyncThunk(
  "chat/logInteraction",
  async (note, { rejectWithValue }) => {
    try {
      const res = await logInteraction(note);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

// ── Slice ─────────────────────────────────────────────────

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [], // { role: 'user'|'assistant'|'system', content: string, data?: object }
    status: "idle", // idle | loading | failed
    error: null,
    lastInteractionId: null, // ID of the most recently logged interaction
  },
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({ role: "user", content: action.payload });
    },
    clearChat: (state) => {
      state.messages = [];
      state.status = "idle";
      state.error = null;
      state.lastInteractionId = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Generic chat message handler
      .addCase(sendMessage.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "idle";
        const responseData = action.payload.data || {};
        state.messages.push({
          role: "assistant",
          content: responseData.reply || "No response.",
          toolCalls: responseData.tool_calls || [],
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Agent failed to respond";
        state.messages.push({
          role: "assistant",
          content: `⚠️ Error: ${action.payload || "Something went wrong."}`,
        });
      })
      // Log interaction from chat
      .addCase(logInteractionFromChat.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(logInteractionFromChat.fulfilled, (state, action) => {
        state.status = "idle";
        const responseData = action.payload.data || action.payload || "";
        
        // Extract interaction ID from response if present
        const idMatch = responseData.match?.(/ID:\s*([a-f0-9-]+)/i);
        if (idMatch) {
          state.lastInteractionId = idMatch[1];
        }

        // Add assistant message with the extracted data
        state.messages.push({
          role: "assistant",
          content: responseData,
          type: "interaction_log",
        });
      })
      .addCase(logInteractionFromChat.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Failed to log interaction";
        state.messages.push({
          role: "assistant",
          content: `❌ Error: ${action.payload || "Failed to log interaction"}`,
        });
      });
  },
});

export const { addUserMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;
