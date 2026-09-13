
# import uuid
# import streamlit as st
# import extra_streamlit_components as stx

# from back.config import Config
# from back.rag_graph import RAGGraph
# from back.intent.dialogue_manager import DialogueManager
# from components.sidebar import render_sidebar
# from styles.style import load_css
# from components.chat_message import (
#     render_user_message,
#     render_ai_message
# )
# from components.input_box import render_input_box
# from components.status import render_status
# from components.citation import render_citations
# from components.evaluation import render_evaluation
# from components.suggested_questions import render_suggested_questions


# st.navigation([
#     st.Page("app_pages/chat.py", title="گفتگو"),
#     st.Page("app_pages/user_management.py", title="مدیریت کاربران"),
#     st.Page("app_pages/login.py", title="ورود"),
#     st.Page("app_pages/admin_dashboard.py", title="داشبورد ادمین"),
# ])
# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="AI Assistant",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )


# # =========================================================
# # AUTHENTICATION CHECK
# # =========================================================

# if not st.session_state.get("is_authenticated", False):
#     st.switch_page("app_pages/login.py")


# # =========================================================
# # LOAD CSS
# # =========================================================

# load_css()


# # =========================================================
# # RAG SYSTEM
# # =========================================================

# @st.cache_resource
# def initialize_rag():
#     return RAGGraph()


# if "rag_graph" not in st.session_state:
#     with st.spinner("🔄 در حال راه‌اندازی دستیار هوشمند..."):
#         try:
#             st.session_state.rag_graph = initialize_rag()
#         except Exception as e:
#             st.error(f"❌ خطا در راه‌اندازی RAG: {e}")
#             st.stop()


# # =========================================================
# # DIALOGUE MANAGER
# # =========================================================

# @st.cache_resource
# def initialize_dialogue_manager():
#     return DialogueManager()


# if "dialogue_manager" not in st.session_state:
#     st.session_state.dialogue_manager = initialize_dialogue_manager()


# # =========================================================
# # SESSION MANAGEMENT
# # =========================================================

# # سوال در انتظار از پیشنهادها
# if "pending_question" not in st.session_state:
#     st.session_state.pending_question = None

# # فلگ برای نشان دادن اینکه سوال پیشنهادی انتخاب شده
# if "suggestion_selected" not in st.session_state:
#     st.session_state.suggestion_selected = False

# # سوال پیشنهادی که باید در اینپوت باکس نمایش داده شود
# if "suggestion_to_display" not in st.session_state:
#     st.session_state.suggestion_to_display = None

# # لیست تمام سِشن‌های کاربر
# if "user_sessions" not in st.session_state:
#     st.session_state.user_sessions = []

# # سِشن فعال فعلی
# if "current_session_id" not in st.session_state:
#     # بررسی کوکی برای سِشن قبلی
#     cookie_manager = stx.CookieManager()
#     saved_session = cookie_manager.get("current_session_id")
    
#     if saved_session and saved_session in st.session_state.user_sessions:
#         st.session_state.current_session_id = saved_session
#     else:
#         # ایجاد سِشن جدید
#         new_session_id = str(uuid.uuid4())
#         st.session_state.current_session_id = new_session_id
#         st.session_state.user_sessions.append(new_session_id)
#         cookie_manager.set("current_session_id", new_session_id)

# # پیام‌های سِشن فعلی
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # دیکشنری برای نگهداری عنوان هر سِشن (اولین سوال)
# if "session_titles" not in st.session_state:
#     st.session_state.session_titles = {}


# # =========================================================
# # LOAD SESSION MESSAGES
# # =========================================================

# def load_session_messages(session_id):
#     """بارگذاری پیام‌های یک سِشن از دیتابیس"""
#     history = st.session_state.dialogue_manager.get_history(session_id)
#     messages = []
    
#     for msg in history:
#         role = msg.get("role")
#         content = msg.get("content")
#         if role and content:
#             messages.append({"role": role, "content": content})
    
#     return messages


# def save_session_title(session_id, first_question):
#     """ذخیره عنوان سِشن (اولین سوال کاربر)"""
#     if session_id not in st.session_state.session_titles:
#         # محدود کردن طول عنوان
#         title = first_question[:50] + "..." if len(first_question) > 50 else first_question
#         st.session_state.session_titles[session_id] = title


# # =========================================================
# # SIDEBAR
# # =========================================================

# # دریافت لیست سِشن‌ها با عنوان‌شان
# session_list = []
# for session_id in st.session_state.user_sessions:
#     title = st.session_state.session_titles.get(session_id, "گفتگوی جدید")
#     session_list.append({
#         "id": session_id,
#         "title": title
#     })

# # مرتب‌سازی بر اساس آخرین فعالیت (جدیدترین اول)
# session_list.reverse()

# # رندر سایدبار با لیست سِشن‌ها
# selected_session = render_sidebar(
#     sessions=session_list,
#     current_session_id=st.session_state.current_session_id
# )

# # اگر کاربر سِشن دیگری را انتخاب کرد
# if selected_session and selected_session != st.session_state.current_session_id:
#     # ذخیره سِشن فعلی
#     st.session_state.current_session_id = selected_session
    
#     # بارگذاری پیام‌های سِشن جدید
#     st.session_state.messages = load_session_messages(selected_session)
    
#     # ریست کردن فلگ‌ها
#     st.session_state.suggestion_selected = False
#     st.session_state.pending_question = None
#     st.session_state.suggestion_to_display = None
    
#     # به‌روزرسانی کوکی
#     cookie_manager = stx.CookieManager()
#     cookie_manager.set("current_session_id", selected_session)
    
#     st.rerun()


# # =========================================================
# # PASSWORD CHANGE SUCCESS
# # =========================================================

# if st.session_state.pop("password_change_success", False):
#     st.markdown(
#         """
#         <div class="password-success-toast">
#             رمز عبور با موفقیت تغییر کرد.
#         </div>
#         """,
#         unsafe_allow_html=True
#     )


# # =========================================================
# # PROCESSING STATE
# # =========================================================

# if "processing_message" not in st.session_state:
#     st.session_state.processing_message = False

# if "processing_started" not in st.session_state:
#     st.session_state.processing_started = False


# # =========================================================
# # SCROLL STATE
# # =========================================================

# if "scroll_to_bottom" not in st.session_state:
#     st.session_state.scroll_to_bottom = False


# # =========================================================
# # CHAT AREA
# # =========================================================

# selected_question = None

# if not st.session_state.messages:
#     # -----------------------------------------------------
#     # WELCOME
#     # -----------------------------------------------------

#     st.html(
#         """
#         <div class="chat-welcome">
#             <h1>سلام 👋</h1>
#             <h3>سوال خود را از دستیار هوشمند بپرسید</h3>
#             <p>پاسخ‌ها بر اساس اسناد سازمانی تولید می‌شوند.</p>
#         </div>
#         """
#     )

#     # -----------------------------------------------------
#     # INITIAL SUGGESTED QUESTIONS (فقط اگر سوالی انتخاب نشده باشد)
#     # -----------------------------------------------------
    
#     if not st.session_state.suggestion_selected and not st.session_state.pending_question:
#         selected_question = render_suggested_questions(
#             [
#                 "شرایط دریافت مجوز احداث نیروگاه چیست؟",
#                 "مدارک لازم برای احداث نیروگاه چیست؟",
#                 "قوانین اتصال نیروگاه به شبکه چیست؟"
#             ]
#         )
        
#         if selected_question:
#             st.session_state.pending_question = selected_question
#             st.session_state.suggestion_to_display = selected_question
#             st.session_state.suggestion_selected = True
#             st.rerun()

# else:
#     # -----------------------------------------------------
#     # CHAT HISTORY
#     # -----------------------------------------------------

#     for idx, message in enumerate(st.session_state.messages):
#         if message["role"] == "user":
#             render_user_message(message["content"])
            
#         elif message["role"] == "assistant":
#             render_ai_message(message["content"])
            
#             # نمایش منابع (Citations)
#             sources = message.get("sources", [])
#             if sources:
#                 render_citations(sources)
            
#             # نمایش ارزیابی
#             scores = message.get("scores", {})
#             if scores and any(scores.values()):
#                 render_evaluation(scores)
            
#             # نمایش سوالات پیشنهادی (فقط برای آخرین پیام و اگر سوالی انتخاب نشده باشد)
#             if idx == len(st.session_state.messages) - 1:
#                 suggestions = message.get("suggestions", [])
#                 if suggestions and not st.session_state.suggestion_selected and not st.session_state.pending_question:
#                     selected_question = render_suggested_questions(suggestions)
#                     if selected_question:
#                         st.session_state.pending_question = selected_question
#                         st.session_state.suggestion_to_display = selected_question
#                         st.session_state.suggestion_selected = True
#                         st.rerun()


# # =========================================================
# # INPUT BOX با نمایش سوال پیشنهادی
# # =========================================================

# # اگر سوال پیشنهادی برای نمایش وجود دارد، آن را به input_box بدهیم
# suggestion_value = st.session_state.get("suggestion_to_display")

# user_input = render_input_box(default_value=suggestion_value)


# # =========================================================
# # NEW USER MESSAGE FROM INPUT
# # =========================================================

# if user_input:
#     user_input = user_input.strip()

#     if user_input:
#         # اگر در حال پردازش نیستیم
#         if not st.session_state.processing_message:
#             # اگر سوال پیشنهادی در input است، آن را پاک کن
#             if st.session_state.suggestion_to_display:
#                 st.session_state.suggestion_to_display = None
            
#             st.session_state.messages.append({
#                 "role": "user",
#                 "content": user_input
#             })

#             # ذخیره عنوان سِشن (اگر اولین سوال باشد)
#             if len(st.session_state.messages) == 1:
#                 save_session_title(
#                     st.session_state.current_session_id,
#                     user_input
#                 )

#             st.session_state.processing_message = True
#             st.session_state.processing_started = True
#             st.rerun()


# # =========================================================
# # PROCESSING
# # =========================================================

# # اگر سوالی در انتظار باشد یا در حال پردازش باشد
# if st.session_state.pending_question or st.session_state.processing_message:
    
#     # اگر سوال در انتظار است، آن را پردازش کن
#     if st.session_state.pending_question:
#         user_message = st.session_state.pending_question
#         st.session_state.pending_question = None
        
#         # اضافه کردن به تاریخچه
#         st.session_state.messages.append({
#             "role": "user",
#             "content": user_message
#         })
        
#         # ذخیره عنوان سِشن (اگر اولین سوال باشد)
#         if len(st.session_state.messages) == 1:
#             save_session_title(
#                 st.session_state.current_session_id,
#                 user_message
#             )
        
#         st.session_state.processing_message = True
#         st.session_state.processing_started = True
#         st.rerun()
    
#     # پردازش در حال انجام
#     elif st.session_state.processing_message:
#         render_status()

#         try:
#             # آخرین پیام کاربر
#             user_message = None
#             for message in reversed(st.session_state.messages):
#                 if message["role"] == "user":
#                     user_message = message["content"]
#                     break

#             if not user_message:
#                 raise ValueError("پیام کاربر پیدا نشد.")

#             # -------------------------------------------------
#             # RAG
#             # -------------------------------------------------

#             rag = st.session_state.rag_graph

#             result = rag.run(
#                 query=user_message,
#                 session_id=st.session_state.current_session_id,
#                 top_k=st.session_state.get("top_k", Config.TOP_K),
#                 max_retries=st.session_state.get("max_retries", Config.MAX_RETRIES)
#             )

#             # -------------------------------------------------
#             # ANSWER
#             # -------------------------------------------------

#             answer = result.get("answer", "پاسخی تولید نشد.")

#             # -------------------------------------------------
#             # SOURCES (منابع) - استخراج از retrieved_docs
#             # -------------------------------------------------

#             retrieved_docs = result.get("retrieved_docs", [])
#             sources = []
            
#             for doc in retrieved_docs:
#                 metadata = doc.get("metadata", {})
#                 # استخراج نام سند و صفحه
#                 doc_name = metadata.get("document_name") or metadata.get("source") or "بدون عنوان"
#                 page = metadata.get("page") or metadata.get("locator") or "-"
                
#                 sources.append({
#                     "name": doc_name,
#                     "page": page,
#                     "content": doc.get("content", "")[:200]
#                 })

#             # -------------------------------------------------
#             # EVALUATION
#             # -------------------------------------------------

#             validation_result = result.get("validation_result", {}) or {}

#             scores = {
#                 "faithfulness": validation_result.get("faithfulness"),
#                 "relevance": validation_result.get("relevance"),
#                 "completeness": validation_result.get("completeness"),
#                 "overall": validation_result.get("overall_score"),
#             }

#             # -------------------------------------------------
#             # SUGGESTED QUESTIONS
#             # -------------------------------------------------

#             suggestions = result.get("suggested_questions", [])

#             # -------------------------------------------------
#             # SAVE RESPONSE
#             # -------------------------------------------------

#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": answer,
#                 "sources": sources,
#                 "scores": scores,
#                 "suggestions": suggestions,
#                 "details": result
#             })

#             # -------------------------------------------------
#             # FINISHED
#             # -------------------------------------------------

#             st.session_state.processing_message = False
#             st.session_state.processing_started = False
#             st.session_state.scroll_to_bottom = True
            
#             # ریست کردن فلگ‌ها
#             st.session_state.suggestion_selected = False
#             st.session_state.suggestion_to_display = None

#             st.rerun()

#         except Exception as e:
#             st.session_state.processing_message = False
#             st.session_state.processing_started = False
#             st.error(f"❌ خطا در پردازش سؤال:\n\n{str(e)}")


# # =========================================================
# # AUTO SCROLL
# # =========================================================

# if st.session_state.pop("scroll_to_bottom", False):
#     st.markdown(
#         """
#         <script>
#         setTimeout(function() {
#             const container = document.querySelector(
#                 '[data-testid="stAppViewContainer"]'
#             );
#             if (container) {
#                 container.scrollTo({
#                     top: container.scrollHeight,
#                     behavior: "smooth"
#                 });
#             }
#             window.scrollTo({
#                 top: document.body.scrollHeight,
#                 behavior: "smooth"
#             });
#         }, 200);
#         </script>
#         """,
#         unsafe_allow_html=True
#     )

import os
import time
import streamlit as st

from styles.style import load_css


# =========================================================
# PAGE CONFIG (فقط یک‌بار، فقط همین‌جا)
# =========================================================
st.set_page_config(
    page_title="دستیار هوشمند",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# HIDE STREAMLIT DEFAULT UI
# =========================================================
st.markdown(
    """
    <style>
    #MainMenu,
    header,
    footer,
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .block-container {
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# =========================================================
# SESSION STATE
# =========================================================
if "loading_done" not in st.session_state:
    st.session_state.loading_done = False

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# =========================================================
# LOADING PAGE (فقط یک بار)
# =========================================================
if not st.session_state.loading_done:

    st.markdown(
        """
        <style>
        .loading-page {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            direction: rtl;
            background: #212121;
        }

        .loading-container {
            text-align: center;
        }

        .loading-logo {
            width: 72px;
            height: 72px;
            margin: 0 auto 24px;
            border-radius: 20px;
            background: #2F2F2F;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
        }

        .loading-title {
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .loading-subtitle {
            color: #A0A0A0;
            font-size: 14px;
            margin-bottom: 28px;
        }

        .spinner {
            width: 32px;
            height: 32px;
            margin: 0 auto;
            border: 3px solid #3A3A3A;
            border-top: 3px solid #3B82F6;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>

        <div class="loading-page">
            <div class="loading-container">
                <div class="loading-logo">🤖</div>
                <div class="loading-title">در حال آماده‌سازی دستیار</div>
                <div class="loading-subtitle">لطفاً چند لحظه صبر کنید...</div>
                <div class="spinner"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    time.sleep(2)

    st.session_state.loading_done = True
    st.rerun()
    st.stop()


# =========================================================
# NAVIGATION (تنها جایی که صفحات تعریف می‌شوند)
# =========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(CURRENT_DIR, "app_pages")

pages = [
    st.Page(os.path.join(PAGES_DIR, "login.py"), title="ورود"),
    st.Page(os.path.join(PAGES_DIR, "chat.py"), title="گفتگو"),
    st.Page(os.path.join(PAGES_DIR, "user_management.py"), title="مدیریت کاربران"),
    ]

pg = st.navigation(pages, position="hidden")
pg.run()