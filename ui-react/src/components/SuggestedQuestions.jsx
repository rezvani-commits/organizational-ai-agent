/**
 * components/SuggestedQuestions.jsx
 * -----------------------------------
 * معادل components/suggested_questions.py (render_suggested_questions).
 */

export default function SuggestedQuestions({ questions, title = "سوالات پیشنهادی", onSelect }) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="suggested-questions">
      <div className="suggested-questions-title">💡 {title}</div>
      <div className="suggested-questions-list">
        {questions.map((question, idx) => (
          <button
            key={idx}
            type="button"
            className="suggested-question"
            onClick={() => onSelect?.(question)}
          >
            <span className="suggested-question-icon">↗</span>
            <span>{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
