import { configureStore } from "@reduxjs/toolkit";
import interactionReducer from "../features/interactionSlice";
import chatReducer from "../features/chatSlice";
import hcpReducer from "../features/hcpSlice";

export const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    chat: chatReducer,
    hcp: hcpReducer,
  },
});
