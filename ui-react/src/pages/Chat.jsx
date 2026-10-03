import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import Sidebar from "../components/Sidebar";
import { UserMessage, AIMessage } from "../components/ChatMessage";
import Citations from "../components/Citation";
import Evaluation from "../components/Evaluation";
import SuggestedQuestions from "../components/SuggestedQuestions";
import InputBox from "../components/InputBox";
import { StatusLive, StatusFinal } from "../components/Status";
import { cookieManager } from "../components/cookieManager";
import {
  createSession,
  listSessions,
  setSessionTitle,
  touchSession,
  deleteSession,
  getHistory,
  saveHistory,
} from "../data/sessionStore";
// import { getMockResponse } from "../data/mockData";
import { askQuestion } from "../data/api";

const INITIAL_SUGGESTIONS = [
  "اگر کارگر برای ارتقای سطح صلاحیت حرفه‌ای امتیاز لازم را نگیرد، چه زمانی می‌تواند دوباره معرفی شود؟",
  "هزینه دندانپزشکی کارکنان و افراد تحت تکفل تا چه مبلغی تحت پوشش بیمه است؟",
  "هزینه خرید عینک یا لنز طبی برای بیمه‌شدگان چقدر پوشش داده می‌شود؟",
];

function newSessionId() {
  return crypto.randomUUID();
}

/**
 * pages/Chat.jsx
 * -----------------
 * معادل app_pages/chat.py.
 *
 * @param {() => void} onNavigateUserManagement
 */
export default function Chat({ onNavigateUserManagement }) {
  const { user } = useAuth();
  const username = user.username;

  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);

  const [suggestionSelected, setSuggestionSelected] = useState(false);
  const [suggestionToDisplay, setSuggestionToDisplay] = useState(null);

  const [processing, setProcessing] = useState(false);
  const [statusLabel, setStatusLabel] = useState("");
  const [statusDone, setStatusDone] = useState(false);
  const [statusError, setStatusError] = useState(null);

  const bottomRef = useRef(null);

  // =====================================================
  // INITIAL SESSION (بازیابی از کوکی یا ایجاد سشن جدید)
  // =====================================================

  useEffect(() => {
    const dbSessions = listSessions(username);
    setSessions(dbSessions);

    const savedSession = cookieManager.get("current_session_id");
    const sessionIds = dbSessions.map((s) => s.id);

    if (savedSession && sessionIds.includes(savedSession)) {
      setCurrentSessionId(savedSession);
      setMessages(getHistory(savedSession));
    } else {
      const id = newSessionId();
      createSession(id, username);
      cookieManager.set("current_session_id", id);
      setCurrentSessionId(id);
      setMessages([]);
      setSessions(listSessions(username));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (messages.length && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, processing]);

  // =====================================================
  // SESSION ACTIONS
  // =====================================================

  function handleNewSession() {
    const id = newSessionId();
    createSession(id, username);
    cookieManager.set("current_session_id", id);
    setCurrentSessionId(id);
    setMessages([]);
    setSessions(listSessions(username));
    resetSuggestionState();
  }

  function handleSelectSession(sessionId) {
    if (sessionId === currentSessionId) return;
    setCurrentSessionId(sessionId);
    setMessages(getHistory(sessionId));
    cookieManager.set("current_session_id", sessionId);
    resetSuggestionState();
  }

  function handleDeleteSession(sessionId) {
    deleteSession(sessionId);

    if (sessionId === currentSessionId) {
      const id = newSessionId();
      createSession(id, username);
      cookieManager.set("current_session_id", id);
      setCurrentSessionId(id);
      setMessages([]);
    }

    setSessions(listSessions(username));
  }

  function resetSuggestionState() {
    setSuggestionSelected(false);
    setSuggestionToDisplay(null);
  }

  // =====================================================
  // SEND MESSAGE
  // =====================================================

  async function handleSend(text) {
    if (!text || processing) return;

    setSuggestionToDisplay(null);

    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    saveHistory(currentSessionId, nextMessages);

    if (nextMessages.length === 1) {
      setSessionTitle(currentSessionId, text);
    }
    touchSession(currentSessionId);
    setSessions(listSessions(username));

    await runAssistant(text, nextMessages);
  }

  function handleSelectSuggestion(question) {
    setSuggestionToDisplay(question);
    setSuggestionSelected(true);
  }

  async function runAssistant(userMessage, messagesSoFar) {
    setProcessing(true);
    setStatusDone(false);
    setStatusError(null);
    setStatusLabel("");

    try {
      // const result = await getMockResponse(userMessage, (step) => setStatusLabel(step));
      const result = await askQuestion(
            userMessage,
              currentSessionId,
              user.level ?? null,
              (step) => setStatusLabel(step)
            );

      setStatusDone(true);

      const updated = [
        ...messagesSoFar,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources || [],
          scores: result.scores || {},
          suggestions: result.suggestions || [],
        },
      ];

      setMessages(updated);
      saveHistory(currentSessionId, updated);

      setSuggestionSelected(false);
      setSuggestionToDisplay(null);
    } catch (err) {
      setStatusError(err?.message || "خطای ناشناخته");
    } finally {
      setProcessing(false);
    }
  }

  // =====================================================
  // RENDER
  // =====================================================

  const sidebarProps = {
    sessions,
    currentSessionId,
    onSelectSession: handleSelectSession,
    onNewSession: handleNewSession,
    onDeleteSession: handleDeleteSession,
  };

  const showWelcome = messages.length === 0;
  const lastMessage = messages[messages.length - 1];
  const showLastSuggestions =
    lastMessage?.role === "assistant" &&
    lastMessage.suggestions?.length > 0 &&
    !suggestionSelected &&
    !processing;

  return (
    <div className="page-with-sidebar">
      <Sidebar {...sidebarProps} onNavigateUserManagement={onNavigateUserManagement} />

      <main className="chat-main">
        <div className="chat-scroll-area">
          {showWelcome ? (
            <>
              <div className="chat-welcome">
                <h1>سلام</h1>
                <h3>سوال خود را از نیرویار بپرسید</h3>
                <p>پاسخ‌ها بر اساس اسناد سازمانی تولید می‌شوند.</p>
              </div>

              {!suggestionSelected && !suggestionToDisplay && (
                <SuggestedQuestions
                  questions={INITIAL_SUGGESTIONS}
                  onSelect={handleSelectSuggestion}
                />
              )}
            </>
          ) : (
            messages.map((message, idx) => {
              if (message.role === "user") {
                return <UserMessage key={idx} message={message.content} />;
              }
              return (
                <div key={idx}>
                  <AIMessage answer={message.content} />
                  {message.sources?.length > 0 && <Citations sources={message.sources} />}
                  {message.scores && Object.values(message.scores).some(Boolean) && (
                    <Evaluation scores={message.scores} />
                  )}
                  {idx === messages.length - 1 && showLastSuggestions && (
                    <SuggestedQuestions
                      questions={message.suggestions}
                      onSelect={handleSelectSuggestion}
                    />
                  )}
                </div>
              );
            })
          )}

          {processing && (
            <>{statusError ? (
              <StatusLive currentLabel="" isError errorMessage={statusError} />
            ) : statusDone ? (
              <StatusFinal />
            ) : (
              <StatusLive currentLabel={statusLabel} />
            )}</>
          )}

          <div ref={bottomRef} />
        </div>

        <InputBox
          disabled={processing}
          defaultValue={suggestionToDisplay}
          onSubmit={handleSend}
        />
      </main>
    </div>
  );
}
