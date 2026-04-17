import LogInteractionForm from "./components/LogInteractionForm";
import ChatPanel from "./components/ChatPanel";
import "./App.css";

function App() {
  return (
    <div className="app">
      <div className="app-container">
        {/* Left Panel: Form */}
        <div className="app-left-panel">
          <LogInteractionForm />
        </div>

        {/* Right Panel: Chat */}
        <div className="app-right-panel">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
