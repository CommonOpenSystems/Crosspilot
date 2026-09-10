import { useEffect, useRef, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

type Role = "user" | "assistant";

interface Message {
  id: number;
  role: Role;
  text: string;
}

let nextId = 1;

function App() {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [content, setContent] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Hide window on Escape
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        await getCurrentWindow().hide();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Send on Enter, newline on Shift+Enter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [content]);

  // Focus textarea when shown
  useEffect(() => {
    const unlisten = listen("crosspilot://show", () => {
      textareaRef.current?.focus();
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  // Clear on hide
  useEffect(() => {
    const unlisten = listen("crosspilot://hide", () => {
      setContent("");
      setMessages([]);
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  function sendMessage() {
    const text = content.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { id: nextId++, role: "user", text }]);
    setContent("");
    // Placeholder assistant reply
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: nextId++, role: "assistant", text: "…" },
      ]);
    }, 500);
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <span className="chat-title">Crosspilot</span>
        <button className="close-btn" onClick={() => getCurrentWindow().hide()}>✕</button>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <p className="empty-hint">Send a message to get started.</p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`message message--${msg.role}`}>
            <span className="message-label">
              {msg.role === "user" ? "You" : "Assistant"}
            </span>
            <p className="message-text">{msg.text}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="input"
          placeholder="Message… (Enter to send)"
          spellCheck={false}
          rows={1}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <button className="send-btn" onClick={sendMessage}>↑</button>
      </div>
    </div>
  );
}

export default App;
