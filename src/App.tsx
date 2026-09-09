import { useEffect, useRef, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

function App() {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [content, setContent] = useState("");

  // Hide window and clear content on Escape
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        const win = getCurrentWindow();
        setContent("");
        await win.hide();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus textarea when window is shown via shortcut
  useEffect(() => {
    const unlisten = listen("crosspilot://show", () => {
      textareaRef.current?.focus();
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  // Clear textarea when window is hidden via shortcut
  useEffect(() => {
    const unlisten = listen("crosspilot://hide", () => {
      setContent("");
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  return (
    <div className="popup">
      <span className="label">Test Popup</span>
      <textarea
        ref={textareaRef}
        className="editor"
        placeholder="Start typing..."
        spellCheck={false}
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
    </div>
  );
}

export default App;
