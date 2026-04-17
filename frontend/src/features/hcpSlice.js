import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { searchHCPs, getHCPHistory } from "../api/api";

// ── Async Thunks ──────────────────────────────────────────

export const searchHCP = createAsyncThunk(
  "hcp/search",
  async (query, { rejectWithValue }) => {
    try {
      const res = await searchHCPs(query);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

export const fetchHCPHistory = createAsyncThunk(
  "hcp/fetchHistory",
  async ({ hcpId, limit = 10 }, { rejectWithValue }) => {
    try {
      const res = await getHCPHistory(hcpId, limit);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

// ── Slice ─────────────────────────────────────────────────

const hcpSlice = createSlice({
  name: "hcp",
  initialState: {
    searchResults: [],
    searchQuery: "",
    history: null,
    searchStatus: "idle",
    historyStatus: "idle",
    error: null,
  },
  reducers: {
    setSearchQuery: (state, action) => {
      state.searchQuery = action.payload;
    },
    clearSearch: (state) => {
      state.searchResults = [];
      state.searchQuery = "";
      state.searchStatus = "idle";
    },
    clearHistory: (state) => {
      state.history = null;
      state.historyStatus = "idle";
    },
  },
  extraReducers: (builder) => {
    builder
      // Search
      .addCase(searchHCP.pending, (state) => {
        state.searchStatus = "loading";
      })
      .addCase(searchHCP.fulfilled, (state, action) => {
        state.searchStatus = "succeeded";
        // Parse the search result text into structured items
        const data = action.payload.data || "";
        const lines = data
          .split("\n")
          .filter((l) => l.startsWith("•"))
          .map((l) => {
            const parts = l.replace("• ", "").split(" | ");
            return {
              name: parts[0]?.trim() || "",
              specialty: parts[1]?.trim() || "",
              hospital: parts[2]?.trim() || "",
              location: parts[3]?.trim() || "",
              id: parts[4]?.replace("ID: ", "").trim() || "",
            };
          });
        state.searchResults = lines;
      })
      .addCase(searchHCP.rejected, (state, action) => {
        state.searchStatus = "failed";
        state.error = action.payload;
      })
      // History
      .addCase(fetchHCPHistory.pending, (state) => {
        state.historyStatus = "loading";
      })
      .addCase(fetchHCPHistory.fulfilled, (state, action) => {
        state.historyStatus = "succeeded";
        state.history = action.payload.data;
      })
      .addCase(fetchHCPHistory.rejected, (state, action) => {
        state.historyStatus = "failed";
        state.error = action.payload;
      });
  },
});

export const { setSearchQuery, clearSearch, clearHistory } = hcpSlice.actions;
export default hcpSlice.reducer;
