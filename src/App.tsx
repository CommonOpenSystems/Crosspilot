import { useEffect, useRef } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import "./App.css";

function App() {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus the textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Close window on Escape
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        const win = getCurrentWindow();
        await win.close();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="popup">
      <span className="label">Test Popup</span>
      <textarea
        ref={textareaRef}
        className="editor"
        placeholder="Start typing..."
        spellCheck={false}
      />
    </div>
  );
}

export default App;
