import uuid
import requests
import streamlit as st
import extra_streamlit_components as stx

from back.config import Config
from back.intent.dialogue_manager import DialogueManager
from back.session_store import (
    create_session,
    list_sessions,
    set_session_title,
    touch_session
)
from auth.auth import get_current_user
from components.sidebar import render_sidebar
from components.cookie_manager import get_cookie_manager
from styles.style import load_css
from components.chat_message import (
    render_user_message,
    render_ai_message
)
from components.input_box import render_input_box
from components.status import render_status
from components.citation import render_citations
from components.evaluation import render_evaluation
from components.suggested_questions import render_suggested_questions


import threading
import time as time_module
from components.status import render_status_live, render_status_final


# =========================================================
# BACKEND CONFIG
# =========================================================

BACKEND_URL = "http://127.0.0.1:8080"


# =========================================================
# AUTHENTICATION CHECK
# =========================================================

if not st.session_state.get("is_authenticated", False):
    st.switch_page("app_pages/login.py")


# =========================================================
# LOAD CSS
# =========================================================

load_css()


# =========================================================
# DIALOGUE MANAGER
# =========================================================

@st.cache_resource
def initialize_dialogue_manager():
    return DialogueManager()


if "dialogue_manager" not in st.session_state:
    st.session_state.dialogue_manager = initialize_dialogue_manager()


# =========================================================
# SESSION MANAGEMENT
# =========================================================

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "suggestion_selected" not in st.session_state:
    st.session_state.suggestion_selected = False

if "suggestion_to_display" not in st.session_state:
    st.session_state.suggestion_to_display = None


# =========================================================
# DATABASE SESSION MANAGEMENT
# =========================================================

username = get_current_user()["username"]
user_access_level = get_current_user().get("level", 1)


def load_session_messages(session_id):
    history = st.session_state.dialogue_manager.get_history(session_id)
    messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if role and content:
            messages.append({"role": role, "content": content})
    return messages


if "current_session_id" not in st.session_state:

    cookie_manager = get_cookie_manager()
    all_cookies = cookie_manager.get_all()

    if all_cookies is None:
        st.stop()

    saved_session = all_cookies.get("current_session_id")

    db_sessions = list_sessions(username)
    session_ids = [session["id"] for session in db_sessions]

    if saved_session and saved_session in session_ids:
        st.session_state.current_session_id = saved_session
        st.session_state.messages = load_session_messages(saved_session)
    else:
        new_session_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_session_id
        create_session(new_session_id, username)
        cookie_manager.set("current_session_id", new_session_id)

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# SIDEBAR
# =========================================================

session_list = list_sessions(username)

selected_session = render_sidebar(
    sessions=session_list,
    current_session_id=st.session_state.current_session_id
)

if selected_session and selected_session != st.session_state.current_session_id:

    st.session_state.current_session_id = selected_session
    st.session_state.messages = load_session_messages(selected_session)

    st.session_state.suggestion_selected = False
    st.session_state.pending_question = None
    st.session_state.suggestion_to_display = None

    cookie_manager = get_cookie_manager()
    cookie_manager.set("current_session_id", selected_session)

    st.rerun()


# =========================================================
# PASSWORD CHANGE SUCCESS
# =========================================================

if st.session_state.pop("password_change_success", False):
    st.markdown(
        """
        <div class="password-success-toast">
            رمز عبور با موفقیت تغییر کرد.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# PROCESSING STATE
# =========================================================

if "processing_message" not in st.session_state:
    st.session_state.processing_message = False

if "processing_started" not in st.session_state:
    st.session_state.processing_started = False


# =========================================================
# SCROLL STATE
# =========================================================

if "scroll_to_bottom" not in st.session_state:
    st.session_state.scroll_to_bottom = False


# =========================================================
# CHAT AREA
# =========================================================

selected_question = None

if not st.session_state.messages:
    st.html(
        """
        <div class="chat-welcome">
            <h1>سلام 👋</h1>
            <h3>سوال خود را از دستیار هوشمند بپرسید</h3>
            <p>پاسخ‌ها بر اساس اسناد سازمانی تولید می‌شوند.</p>
        </div>
        """
    )

    if not st.session_state.suggestion_selected and not st.session_state.pending_question:
        selected_question = render_suggested_questions(
            [
                "شرایط دریافت مجوز احداث نیروگاه چیست؟",
                "مدارک لازم برای احداث نیروگاه چیست؟",
                "قوانین اتصال نیروگاه به شبکه چیست؟"
            ]
        )

        if selected_question:
            st.session_state.pending_question = selected_question
            st.session_state.suggestion_to_display = selected_question
            st.session_state.suggestion_selected = True
            st.rerun()

else:
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            render_user_message(message["content"])

        elif message["role"] == "assistant":
            render_ai_message(message["content"])

            sources = message.get("sources", [])
            if sources:
                render_citations(sources)

            scores = message.get("scores", {})
            if scores and any(scores.values()):
                render_evaluation(scores)

            if idx == len(st.session_state.messages) - 1:
                suggestions = message.get("suggestions", [])
                if suggestions and not st.session_state.suggestion_selected and not st.session_state.pending_question:
                    selected_question = render_suggested_questions(suggestions)
                    if selected_question:
                        st.session_state.pending_question = selected_question
                        st.session_state.suggestion_to_display = selected_question
                        st.session_state.suggestion_selected = True
                        st.rerun()


# =========================================================
# INPUT BOX
# =========================================================

suggestion_value = st.session_state.get("suggestion_to_display")

user_input = render_input_box(default_value=suggestion_value)


# =========================================================
# NEW USER MESSAGE FROM INPUT
# =========================================================

if user_input:
    user_input = user_input.strip()

    if user_input:
        if not st.session_state.processing_message:
            if st.session_state.suggestion_to_display:
                st.session_state.suggestion_to_display = None

            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })

            if len(st.session_state.messages) == 1:
                set_session_title(
                    st.session_state.current_session_id,
                    user_input
                )

            touch_session(st.session_state.current_session_id)

            st.session_state.processing_message = True
            st.session_state.processing_started = True
            st.rerun()


# =========================================================
# PROCESSING
# =========================================================

if st.session_state.pending_question or st.session_state.processing_message:

    if st.session_state.pending_question:
        user_message = st.session_state.pending_question
        st.session_state.pending_question = None

        st.session_state.messages.append({
            "role": "user",
            "content": user_message
        })

        if len(st.session_state.messages) == 1:
            set_session_title(
                st.session_state.current_session_id,
                user_message
            )

        touch_session(st.session_state.current_session_id)
        st.session_state.suggestion_to_display = None

        st.session_state.processing_message = True
        st.session_state.processing_started = True
        st.rerun()

    elif st.session_state.processing_message:

        user_message = None
        for message in reversed(st.session_state.messages):
            if message["role"] == "user":
                user_message = message["content"]
                break

        if not user_message:
            st.session_state.processing_message = False
            st.session_state.processing_started = False
            st.error("❌ پیام کاربر پیدا نشد.")
        else:
            session_id = st.session_state.current_session_id

            # نگه‌دارنده‌ی نتیجه، مشترک بین ترد پس‌زمینه و ترد اصلی
            run_holder = {"done": False, "result": None, "error": None}

            def _run_rag():
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/ask",
                        json={
                            "query": user_message,
                            "session_id": session_id,
                            "top_k": st.session_state.get("top_k", Config.TOP_K),
                            "max_retries": st.session_state.get("max_retries", Config.MAX_RETRIES),
                            "user_access_level": user_access_level,
                        },
                        timeout=120,
                    )
                    response.raise_for_status()
                    run_holder["result"] = response.json()
                except Exception as exc:
                    run_holder["error"] = str(exc)
                finally:
                    run_holder["done"] = True

            worker = threading.Thread(target=_run_rag, daemon=True)
            worker.start()

            # ترد اصلی: هر ۰.۴ ثانیه وضعیت رو از بک‌اند می‌خونه و ویجت رو آپدیت می‌کنه
            status_placeholder = st.empty()
            POLL_INTERVAL = 0.4
            POLL_TIMEOUT = 60
            poll_start = time_module.time()
            timed_out = False

            while not run_holder["done"]:
                try:
                    status_resp = requests.get(f"{BACKEND_URL}/status/{session_id}", timeout=5)
                    entry = status_resp.json() if status_resp.ok else None
                except Exception:
                    entry = None

                if entry and entry.get("step") == "error":
                    render_status_live(
                        status_placeholder, "", is_error=True,
                        error_message=entry.get("error_message", ""),
                    )
                    break

                render_status_live(status_placeholder, entry.get("step") if entry else "در حال پردازش")

                if time_module.time() - poll_start > POLL_TIMEOUT:
                    timed_out = True
                    break

                time_module.sleep(POLL_INTERVAL)

            if timed_out and not run_holder["done"]:
                st.session_state.processing_message = False
                st.session_state.processing_started = False
                st.error("❌ پردازش بیش از حد طول کشید. لطفاً دوباره تلاش کنید.")

            elif run_holder["error"]:
                st.session_state.processing_message = False
                st.session_state.processing_started = False
                st.error(f"❌ خطا در پردازش سؤال:\n\n{run_holder['error']}")

            else:
                render_status_final(status_placeholder)
                result = run_holder["result"]

                answer = result.get("answer", "پاسخی تولید نشد.")
                is_not_found = Config.NOT_FOUND_PHRASE.strip() in answer.strip()

                retrieved_docs = result.get("retrieved_docs", [])
                sources = []
                if not is_not_found:
                    for doc in retrieved_docs:
                        metadata = doc.get("metadata", {})
                        doc_access_level = metadata.get("access_level")
                        if doc_access_level is not None and doc_access_level > user_access_level:
                            continue
                        doc_name = metadata.get("document_name") or metadata.get("source") or "بدون عنوان"
                        page = metadata.get("page") or metadata.get("locator") or "-"
                        sources.append({
                            "name": doc_name,
                            "page": page,
                            "content": doc.get("content", "")[:200]
                        })

                validation_result = result.get("validation_result", {}) or {}
                scores = {
                    "faithfulness": validation_result.get("faithfulness"),
                    "relevance": validation_result.get("relevance"),
                    "completeness": validation_result.get("completeness"),
                    "overall": validation_result.get("overall_score"),
                }

                suggestions = result.get("suggested_questions", [])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "scores": scores,
                    "suggestions": suggestions,
                    "details": result
                })

                st.session_state.processing_message = False
                st.session_state.processing_started = False
                st.session_state.scroll_to_bottom = True
                st.session_state.suggestion_selected = False
                st.session_state.suggestion_to_display = None

                st.rerun()


# =========================================================
# AUTO SCROLL
# =========================================================

if st.session_state.pop("scroll_to_bottom", False):
    st.markdown(
        """
        <script>
        setTimeout(function() {
            const container = document.querySelector(
                '[data-testid="stAppViewContainer"]'
            );
            if (container) {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: "smooth"
                });
            }
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: "smooth"
            });
        }, 200);
        </script>
        """,
        unsafe_allow_html=True
    )