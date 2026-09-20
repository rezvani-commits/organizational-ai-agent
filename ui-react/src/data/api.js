const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// const STEP_LABELS = {
//   fast_intent_check: "بررسی اولیه پیام",
//   rewrite_query: "بازنویسی سوال",
//   analyze_query: "تحلیل سوال",
//   process_multi_query: "پردازش چند سوال",
//   retrieve: "جستجو در اسناد",
//   generate_context: "آماده‌سازی اطلاعات مرتبط",
//   generate_answer: "تولید پاسخ",
//   response_validator: "ارزیابی پاسخ",
//   no_docs_response: "بررسی نتیجه جستجو",
//   direct_response: "آماده‌سازی پاسخ",
//   calculator: "محاسبه",
//   calendar: "بررسی تاریخ",
//   clarify: "آماده‌سازی سوال تکمیلی",
//   summarize: "خلاصه‌سازی",
//   compare: "مقایسه اطلاعات",
// };

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function askQuestion(query, sessionId, accessLevel, onStep) {
  let polling = true;

  (async function pollStatus() {
    while (polling) {
      try {
        const res = await fetch(`${API_BASE}/status/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (data?.step && data.step !== "error") {
            onStep?.(data.step);
            }
        }
      } catch {
        // خطای موقت polling مهم نیست
      }
      await sleep(400);
    }
  })();

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        user_access_level: accessLevel ?? null,
      }),
    });

    if (!res.ok) {
      let detail = `خطای سرور (${res.status})`;
      try {
        const errBody = await res.json();
        detail = errBody.detail || detail;
      } catch {}
      throw new Error(detail);
    }

    const data = await res.json();

    return {
      answer: data.answer,
      sources: data.sources || [],
      scores: data.scores || {},
      suggestions: data.suggestions || [],
      warning: data.warning || null,
      metadata: {
        processing_time: data.processing_time,
        intent: data.intent,
        was_rewritten: data.was_rewritten,
      },
    };
  } finally {
    polling = false;
  }
}