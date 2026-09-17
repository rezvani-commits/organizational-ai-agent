import uuid
import streamlit as st
import extra_streamlit_components as stx

from back.config import Config
from back.rag_graph import RAGGraph
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
import time as time_module  # چون time قبلاً برای چیز دیگه‌ای import نشده تو این فایل - اگه شده، همون رو استفاده کن
from back import status_store
from components.status import render_status_live, render_status_final


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
# RAG SYSTEM
# =========================================================

@st.cache_resource
def initialize_rag():
    return RAGGraph()


if "rag_graph" not in st.session_state:
    with st.spinner("🔄 در حال راه‌اندازی دستیار هوشمند..."):
        try:
            st.session_state.rag_graph = initialize_rag()
        except Exception as e:
            st.error(f"❌ خطا در راه‌اندازی RAG: {e}")
            st.stop()


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

# سوال در انتظار از پیشنهادها
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# فلگ برای نشان دادن اینکه سوال پیشنهادی انتخاب شده
if "suggestion_selected" not in st.session_state:
    st.session_state.suggestion_selected = False

# سوال پیشنهادی که باید در اینپوت باکس نمایش داده شود
if "suggestion_to_display" not in st.session_state:
    st.session_state.suggestion_to_display = None


# =========================================================
# DATABASE SESSION MANAGEMENT
# =========================================================

# کاربر لاگین‌شده
username = get_current_user()["username"]
user_access_level = get_current_user().get("level", 1)


def load_session_messages(session_id):
    """بارگذاری پیام‌های یک سِشن از دیتابیس"""
    history = st.session_state.dialogue_manager.get_history(session_id)
    messages = []

    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if role and content:
            messages.append({"role": role, "content": content})

    return messages


# ایجاد یا بازیابی سشن فعلی
if "current_session_id" not in st.session_state:

    cookie_manager = get_cookie_manager()

    # مهم: در اولین اجرای اسکریپت بعد از لود صفحه، کامپوننت کوکی هنوز
    # sync نشده و get_all() مقدار None برمی‌گردونه حتی اگه کوکی واقعاً
    # وجود داشته باشه. اگه همین‌جا تصمیم بگیریم، هر رفرش یک سشن خالی
    # جدید می‌سازه. پس صبر می‌کنیم تا مقدار واقعی آماده بشه.
    all_cookies = cookie_manager.get_all()

    if all_cookies is None:
        st.stop()

    saved_session = all_cookies.get("current_session_id")

    # سشن‌های موجود در دیتابیس برای این کاربر
    db_sessions = list_sessions(username)
    session_ids = [session["id"] for session in db_sessions]

    if saved_session and saved_session in session_ids:
        # بازیابی سشن قبلی
        st.session_state.current_session_id = saved_session

        # بارگذاری پیام‌های قبلی
        st.session_state.messages = load_session_messages(saved_session)
    else:
        # ایجاد سشن جدید
        new_session_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_session_id

        create_session(new_session_id, username)
        cookie_manager.set("current_session_id", new_session_id)

# پیام‌های سِشن فعلی
if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# SIDEBAR
# =========================================================

# دریافت سشن‌های کاربر از دیتابیس
session_list = list_sessions(username)

# رندر سایدبار با لیست سِشن‌ها
selected_session = render_sidebar(
    sessions=session_list,
    current_session_id=st.session_state.current_session_id
)

# اگر کاربر سشن دیگری را انتخاب کرد
if selected_session and selected_session != st.session_state.current_session_id:

    st.session_state.current_session_id = selected_session

    # بارگذاری پیام‌های سشن جدید
    st.session_state.messages = load_session_messages(selected_session)

    # ریست کردن فلگ‌ها
    st.session_state.suggestion_selected = False
    st.session_state.pending_question = None
    st.session_state.suggestion_to_display = None

    # به‌روزرسانی کوکی
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
    # -----------------------------------------------------
    # WELCOME
    # -----------------------------------------------------

    st.html(
        """
        <div class="chat-welcome">
            <h1>سلام 👋</h1>
            <h3>سوال خود را از دستیار هوشمند بپرسید</h3>
            <p>پاسخ‌ها بر اساس اسناد سازمانی تولید می‌شوند.</p>
        </div>
        """
    )

    # -----------------------------------------------------
    # INITIAL SUGGESTED QUESTIONS (فقط اگر سوالی انتخاب نشده باشد)
    # -----------------------------------------------------

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
    # -----------------------------------------------------
    # CHAT HISTORY
    # -----------------------------------------------------

    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            render_user_message(message["content"])

        elif message["role"] == "assistant":
            render_ai_message(message["content"])

            # نمایش منابع (Citations)
            sources = message.get("sources", [])
            if sources:
                render_citations(sources)

            # نمایش ارزیابی
            scores = message.get("scores", {})
            if scores and any(scores.values()):
                render_evaluation(scores)

            # نمایش سوالات پیشنهادی (فقط برای آخرین پیام و اگر سوالی انتخاب نشده باشد)
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
# INPUT BOX با نمایش سوال پیشنهادی
# =========================================================

# اگر سوال پیشنهادی برای نمایش وجود دارد، آن را به input_box بدهیم
suggestion_value = st.session_state.get("suggestion_to_display")

user_input = render_input_box(default_value=suggestion_value)


# =========================================================
# NEW USER MESSAGE FROM INPUT
# =========================================================

if user_input:
    user_input = user_input.strip()

    if user_input:
        # اگر در حال پردازش نیستیم
        if not st.session_state.processing_message:
            # اگر سوال پیشنهادی در input است، آن را پاک کن
            if st.session_state.suggestion_to_display:
                st.session_state.suggestion_to_display = None

            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })

            # اگر اولین سوال این سشن است، عنوان را ذخیره کن
            if len(st.session_state.messages) == 1:
                set_session_title(
                    st.session_state.current_session_id,
                    user_input
                )

            # بروزرسانی زمان آخرین فعالیت سشن
            touch_session(st.session_state.current_session_id)

            st.session_state.processing_message = True
            st.session_state.processing_started = True
            st.rerun()


# =========================================================
# PROCESSING
# =========================================================

# اگر سوالی در انتظار باشد یا در حال پردازش باشد
if st.session_state.pending_question or st.session_state.processing_message:

    # اگر سوال در انتظار است، آن را پردازش کن
    if st.session_state.pending_question:
        user_message = st.session_state.pending_question
        st.session_state.pending_question = None

        # اضافه کردن به تاریخچه
        st.session_state.messages.append({
            "role": "user",
            "content": user_message
        })

        # اگر اولین سوال این سشن است، عنوان را ذخیره کن
        if len(st.session_state.messages) == 1:
            set_session_title(
                st.session_state.current_session_id,
                user_message
            )

        # بروزرسانی آخرین فعالیت سشن
        touch_session(st.session_state.current_session_id)

        # پاک کردن سوال پیشنهادی از input box، تا در حین
        # پردازش دیگر باکس متن + دکمه ارسال نمایش داده نشود
        st.session_state.suggestion_to_display = None

        st.session_state.processing_message = True
        st.session_state.processing_started = True
        st.rerun()


    elif st.session_state.processing_message:

        # آخرین پیام کاربر
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
            rag = st.session_state.rag_graph

            # نگه‌دارنده‌ی نتیجه، مشترک بین ترد پس‌زمینه و ترد اصلی
            run_holder = {"done": False, "result": None, "error": None}

            def _run_rag():
                try:
                    res = rag.run(
                        query=user_message,
                        session_id=session_id,
                        top_k=st.session_state.get("top_k", Config.TOP_K),
                        max_retries=st.session_state.get("max_retries", Config.MAX_RETRIES),
                        user_access_level=user_access_level,
                        on_step=lambda node_name: status_store.set_step(session_id, node_name),
                    )
                    run_holder["result"] = res
                except Exception as exc:
                    status_store.set_error(session_id, str(exc))
                    run_holder["error"] = str(exc)
                finally:
                    run_holder["done"] = True

            worker = threading.Thread(target=_run_rag, daemon=True)
            worker.start()

            # ترد اصلی: هر ۰.۴ ثانیه وضعیت واقعی رو می‌خونه و ویجت رو آپدیت می‌کنه
            status_placeholder = st.empty()
            POLL_INTERVAL = 0.4
            POLL_TIMEOUT = 60
            poll_start = time_module.time()
            timed_out = False

            while not run_holder["done"]:
                entry = status_store.get_status(session_id)

                if entry and entry["step"] == status_store.ERROR_STEP:
                    render_status_live(
                        status_placeholder, "", is_error=True,
                        error_message=entry.get("error_message", ""),
                    )
                    break

                render_status_live(status_placeholder, entry["step"] if entry else "در حال پردازش")

                if time_module.time() - poll_start > POLL_TIMEOUT:
                    timed_out = True
                    break

                time_module.sleep(POLL_INTERVAL)

            status_store.clear(session_id)

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
                print(f"[UI] retrieved_docs count = {len(retrieved_docs)}")   #موقت
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

























    # # پردازش در حال انجام
    # elif st.session_state.processing_message:
    #     render_status()

    #     try:
    #         # آخرین پیام کاربر
    #         user_message = None
    #         for message in reversed(st.session_state.messages):
    #             if message["role"] == "user":
    #                 user_message = message["content"]
    #                 break

    #         if not user_message:
    #             raise ValueError("پیام کاربر پیدا نشد.")

    #         # -------------------------------------------------
    #         # RAG
    #         # -------------------------------------------------

    #         rag = st.session_state.rag_graph

    #         result = rag.run(
    #             query=user_message,
    #             session_id=st.session_state.current_session_id,
    #             top_k=st.session_state.get("top_k", Config.TOP_K),
    #             max_retries=st.session_state.get("max_retries", Config.MAX_RETRIES)
    #         )

    #         # -------------------------------------------------
    #         # ANSWER
    #         # -------------------------------------------------

    #         answer = result.get("answer", "پاسخی تولید نشد.")

    #         # -------------------------------------------------
    #         # SOURCES (منابع) - استخراج از retrieved_docs
    #         # -------------------------------------------------

    #         retrieved_docs = result.get("retrieved_docs", [])
    #         sources = []

    #         for doc in retrieved_docs:
    #             metadata = doc.get("metadata", {})
    #             # استخراج نام سند و صفحه
    #             doc_name = metadata.get("document_name") or metadata.get("source") or "بدون عنوان"
    #             page = metadata.get("page") or metadata.get("locator") or "-"

    #             sources.append({
    #                 "name": doc_name,
    #                 "page": page,
    #                 "content": doc.get("content", "")[:200]
    #             })

    #         # -------------------------------------------------
    #         # EVALUATION
    #         # -------------------------------------------------

    #         validation_result = result.get("validation_result", {}) or {}

    #         scores = {
    #             "faithfulness": validation_result.get("faithfulness"),
    #             "relevance": validation_result.get("relevance"),
    #             "completeness": validation_result.get("completeness"),
    #             "overall": validation_result.get("overall_score"),
    #         }

    #         # -------------------------------------------------
    #         # SUGGESTED QUESTIONS
    #         # -------------------------------------------------

    #         suggestions = result.get("suggested_questions", [])

    #         # -------------------------------------------------
    #         # SAVE RESPONSE
    #         # -------------------------------------------------

    #         st.session_state.messages.append({
    #             "role": "assistant",
    #             "content": answer,
    #             "sources": sources,
    #             "scores": scores,
    #             "suggestions": suggestions,
    #             "details": result
    #         })

    #         # -------------------------------------------------
    #         # FINISHED
    #         # -------------------------------------------------

    #         st.session_state.processing_message = False
    #         st.session_state.processing_started = False
    #         st.session_state.scroll_to_bottom = True

    #         # ریست کردن فلگ‌ها
    #         st.session_state.suggestion_selected = False
    #         st.session_state.suggestion_to_display = None

    #         st.rerun()

    #     except Exception as e:
    #         st.session_state.processing_message = False
    #         st.session_state.processing_started = False
    #         st.error(f"❌ خطا در پردازش سؤال:\n\n{str(e)}")


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