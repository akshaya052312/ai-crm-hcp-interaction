import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { logInteraction, editInteraction, suggestFollowUp } from "../api/api";

// ── Async Thunks ──────────────────────────────────────────

export const submitInteraction = createAsyncThunk(
  "interaction/submit",
  async (note, { rejectWithValue }) => {
    try {
      const res = await logInteraction(note);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

export const updateInteraction = createAsyncThunk(
  "interaction/update",
  async ({ interactionId, editRequest }, { rejectWithValue }) => {
    try {
      const res = await editInteraction(interactionId, editRequest);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

export const fetchFollowUps = createAsyncThunk(
  "interaction/fetchFollowUps",
  async (interactionId, { rejectWithValue }) => {
    try {
      const res = await suggestFollowUp(interactionId);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

// ── Slice ─────────────────────────────────────────────────

const interactionSlice = createSlice({
  name: "interaction",
  initialState: {
    // Form state
    form: {
      hcpName: "",
      interactionType: "Meeting",
      date: new Date().toISOString().split("T")[0],
      time: "",
      attendees: [],
      topicsDiscussed: "",
      materialsShared: [],
      samplesDistributed: [],
      sentiment: "Neutral",
      outcomes: "",
      followUpActions: "",
    },
    // AI-generated follow-ups (read-only)
    aiFollowUps: [],
    // Last submitted interaction ID
    lastInteractionId: null,
    // Status
    submitStatus: "idle", // idle | loading | succeeded | failed
    followUpStatus: "idle",
    error: null,
    successMessage: "",
  },
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    addAttendee: (state, action) => {
      if (action.payload && !state.form.attendees.includes(action.payload)) {
        state.form.attendees.push(action.payload);
      }
    },
    removeAttendee: (state, action) => {
      state.form.attendees = state.form.attendees.filter((a) => a !== action.payload);
    },
    addMaterial: (state, action) => {
      state.form.materialsShared.push(action.payload);
    },
    removeMaterial: (state, action) => {
      state.form.materialsShared = state.form.materialsShared.filter(
        (_, i) => i !== action.payload
      );
    },
    addSample: (state, action) => {
      state.form.samplesDistributed.push(action.payload);
    },
    removeSample: (state, action) => {
      state.form.samplesDistributed = state.form.samplesDistributed.filter(
        (_, i) => i !== action.payload
      );
    },
    resetForm: (state) => {
      state.form = {
        hcpName: "",
        interactionType: "Meeting",
        date: new Date().toISOString().split("T")[0],
        time: "",
        attendees: [],
        topicsDiscussed: "",
        materialsShared: [],
        samplesDistributed: [],
        sentiment: "Neutral",
        outcomes: "",
        followUpActions: "",
      };
      state.aiFollowUps = [];
      state.lastInteractionId = null;
      state.submitStatus = "idle";
      state.error = null;
      state.successMessage = "";
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Submit interaction
      .addCase(submitInteraction.pending, (state) => {
        state.submitStatus = "loading";
        state.error = null;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.submitStatus = "succeeded";
        state.successMessage = action.payload.message || "Interaction logged!";
        // Try to extract interaction ID from the response data
        const data = action.payload.data || "";
        const idMatch = data.match?.(/ID:\s*([a-f0-9-]+)/i);
        if (idMatch) state.lastInteractionId = idMatch[1];
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.submitStatus = "failed";
        state.error = action.payload || "Failed to submit interaction";
      })
      // Follow-ups
      .addCase(fetchFollowUps.pending, (state) => {
        state.followUpStatus = "loading";
      })
      .addCase(fetchFollowUps.fulfilled, (state, action) => {
        state.followUpStatus = "succeeded";
        const data = action.payload.data || "";
        // Parse numbered suggestions from the response
        const suggestions = data
          .split("\n")
          .filter((line) => /^\s*\d+\./.test(line))
          .map((line) => line.replace(/^\s*\d+\.\s*/, "").trim());
        state.aiFollowUps = suggestions.length > 0 ? suggestions : [data];
      })
      .addCase(fetchFollowUps.rejected, (state, action) => {
        state.followUpStatus = "failed";
        state.error = action.payload || "Failed to generate follow-ups";
      });
  },
});

export const {
  updateFormField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
  addSample,
  removeSample,
  resetForm,
  clearError,
} = interactionSlice.actions;

export default interactionSlice.reducer;
