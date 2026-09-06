import json
import os
import uuid

import streamlit as st

from back.config import Config
from back.rag_graph import RAGGraph


# =========================================================
# Streamlit Configuration
# =========================================================

st.set_page_config(
    page_title="دستیار پاسخگو به اسناد حقوقی/سازمانی",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# Session State
# =========================================================

if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.rag_graph = None
    st.session_state.chat_history = []
    st.session_state.total_docs = 0

# هر browser session یک شناسه‌ی منحصربه‌فرد دارد
# تا تاریخچه‌ی کاربران مختلف با هم قاطی نشود.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# سؤال انتخاب‌شده از پیشنهادها
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# =========================================================
# Helper: نمایش معیارهای ارزیابی (faithfulness / relevance / completeness)
# =========================================================

def render_validation_criteria(validation_result: dict, is_multi_query: bool = False):
    """
    سه معیاری که ResponseValidator با LLM-as-a-Judge می‌سنجه رو نمایش می‌ده.

    نکات:
    - اگه پاسخ از نوع "پیدا نشد" بوده (is_not_found=True)، judge اصلاً صدا
      زده نشده، پس این حالت رو جدا اطلاع می‌دیم.
    - اگه مسیر پاسخ chitchat/direct بوده یا چند سؤال هم‌زمان پردازش شده
      (multi-query)، validation_result معیارهای per-criterion نداره
      (یا برای multi-query فقط یک warning ترکیبی داره)، پس چیزی برای
      نمایش نیست و این رو هم شفاف اعلام می‌کنیم.
    """
    if not validation_result:
        st.caption("ℹ️ برای این پاسخ ارزیابی کیفیت (LLM-as-a-Judge) انجام نشده است.")
        return

    if validation_result.get("is_not_found"):
        st.info("ℹ️ پاسخ از نوع «اطلاعاتی یافت نشد» بوده، بنابراین ارزیابی کیفیت روی آن انجام نشده است.")
        return

    faithfulness = validation_result.get("faithfulness")
    relevance = validation_result.get("relevance")
    completeness = validation_result.get("completeness")

    has_scores = any(
        crit and crit.get("score") is not None
        for crit in (faithfulness, relevance, completeness)
    )

    if not has_scores:
        if is_multi_query:
            st.caption(
                "ℹ️ چون این پیام شامل چند سؤال بود، معیارهای ارزیابی به‌صورت "
                "جداگانه برای هر سؤال محاسبه شده و در این خلاصه نمایش داده نمی‌شود."
            )
        else:
            st.caption("ℹ️ برای این پاسخ ارزیابی کیفیت (LLM-as-a-Judge) انجام نشده است.")
        return

    st.subheader("📊 معیارهای ارزیابی پاسخ")

    criteria = [
        ("🎯 صحت / وفاداری به منبع", faithfulness),
        ("🔍 مرتبط بودن با سؤال", relevance),
        ("📋 کامل بودن پاسخ", completeness),
    ]

    cols = st.columns(3)
    for col, (label, crit) in zip(cols, criteria):
        with col:
            score = (crit or {}).get("score")
            reason = (crit or {}).get("reason")
            st.metric(label, f"{score}/10" if score is not None else "—")
            if reason:
                st.caption(reason)

    overall_score = validation_result.get("overall_score")
    if overall_score is not None:
        st.write(f"**📈 نمره کلی:** {overall_score}/10")


def render_details(det: dict):
    """
    جزئیات یک پاسخ رو نمایش می‌ده - فقط بر اساس کلیدهایی که RAGGraph.run()
    واقعاً برمی‌گردونه (needs_retrieval و route_reason حذف شدن چون اصلاً
    تو خروجی run() وجود نداشتن).
    """
    st.write(f"**⏱️ زمان پردازش:** {det.get('processing_time', 0):.2f} ثانیه")
    st.write(f"**🔄 تعداد تلاش:** {det.get('retry_count', 0)}")
    st.write(
        f"**✅ عبور از بررسی کیفیت:** "
        f"{'بله' if det.get('is_satisfied') else 'خیر (پس از حداکثر تلاش)'}"
    )

    if det.get("was_rewritten"):
        st.write(f"**✏️ سؤال بازنویسی‌شده:** {det.get('standalone_query', '')}")

    st.write(f"**🎯 Intent تشخیص‌داده‌شده:** {det.get('intent') or '—'}")
    if det.get("is_multi_query"):
        st.write(f"**🧩 سؤال ترکیبی:** بله ({len(det.get('sub_queries', []))} بخش)")

    st.divider()

    render_validation_criteria(
        det.get("validation_result"),
        is_multi_query=det.get("is_multi_query", False),
    )

    retrieved_docs = det.get("retrieved_docs")
    if retrieved_docs:
        st.subheader("📄 اسناد بازیابی شده:")
        for i, doc in enumerate(retrieved_docs, 1):
            # نکته: HybridRetriever امتیاز رو تحت کلید "fused_score" برمی‌گردونه، نه "score"
            score = doc.get("fused_score", 0)
            content = doc.get("content", "")
            st.markdown(f"**سند {i}** (امتیاز ترکیبی: `{score:.3f}`)")
            st.caption(content[:300] + "...")


# =========================================================
# Initialize RAG System
# =========================================================

@st.cache_resource
def initialize_system():

    # بررسی API Key
    if not Config.GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY not found in .env file!")
        return None, 0

    # بررسی وجود Chroma store (دیگه ایندکس‌سازی خودکار انجام نمی‌شه؛
    # این پوشه باید از قبل با اسکریپت ایندکس‌سازی جداگانه ساخته شده باشه)
    if not os.path.exists(Config.CHROMA_PATH):
        st.error(
            f"❌ پوشه‌ی Chroma پیدا نشد: {Config.CHROMA_PATH}\n\n"
            f"این نسخه از پروژه دیگه ایندکس‌سازی خودکار انجام نمی‌ده - "
            f"اول باید اسکریپت ساخت Chroma (مثلاً build_chroma.py) رو اجرا کنی."
        )
        return None, 0

    if not os.path.exists(Config.NORMALIZED_DATA_PATH):
        st.error(f"❌ فایل داده‌ی نرمال‌شده پیدا نشد: {Config.NORMALIZED_DATA_PATH}")
        return None, 0

    if not os.path.exists(Config.REGISTRY_PATH):
        st.error(f"❌ فایل رجیستری اسناد پیدا نشد: {Config.REGISTRY_PATH}")
        return None, 0

    # =====================================================
    # RAG Graph
    # HybridRetriever داخل RAGGraph خودش مستقیماً به chromaStore وصل می‌شه
    # و dataNormalized + registry رو می‌خونه - نیازی به VectorStoreManager
    # یا data_loader جدا نیست.
    # =====================================================
    rag_graph = RAGGraph()

    # تعداد اسناد رو مستقیم از فایل نرمال‌شده می‌خونیم (فقط برای نمایش آماری)
    total_docs = 0
    try:
        with open(Config.NORMALIZED_DATA_PATH, encoding="utf-8") as f:
            total_docs = len(json.load(f))
    except Exception:
        pass

    return rag_graph, total_docs


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.title("⚙️ تنظیمات")

    # -----------------------------------------------------
    # Initialize
    # -----------------------------------------------------

    if not st.session_state.initialized:

        with st.spinner("🔄 در حال راه‌اندازی سیستم..."):

            rag_graph, total_docs = initialize_system()

            if rag_graph:

                st.session_state.rag_graph = rag_graph
                st.session_state.total_docs = total_docs
                st.session_state.initialized = True

                st.success("✅ سیستم آماده است!")

            else:
                st.stop()

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📄 اسناد", st.session_state.total_docs)

    with col2:
        st.metric("🔧 مدل", Config.LLM_MODEL)

    # -----------------------------------------------------
    # RAG Settings
    # -----------------------------------------------------

    st.divider()

    top_k = st.slider(
        "تعداد اسناد بازیابی",
        min_value=1,
        max_value=5,
        value=Config.TOP_K
    )

    max_retries = st.slider(
        "حداکثر تلاش",
        min_value=1,
        max_value=3,
        value=Config.MAX_RETRIES
    )

    st.caption(
        "ℹ️ پاسخ پس از عبور از بررسی کیفیت نمایش داده می‌شود."
    )

    # -----------------------------------------------------
    # Clear Chat History
    # -----------------------------------------------------

    if st.button(
        "🗑️ پاک کردن تاریخچه",
        use_container_width=True
    ):

        # پاک کردن تاریخچه‌ی Streamlit
        st.session_state.chat_history = []

        # پاک کردن تاریخچه‌ی Dialogue Manager
        if st.session_state.rag_graph:

            st.session_state.rag_graph.dialogue_manager.clear_session(
                st.session_state.session_id
            )

        st.rerun()


# =========================================================
# Main Page
# =========================================================

st.title("📖 دستیار هوشمند پاسخگو به اسناد حقوقی/سازمانی")

st.caption(
    "پرسش و پاسخ هوشمند بر اساس اسناد داخلی"
)


# =========================================================
# Display Chat History
# =========================================================

for msg_idx, msg in enumerate(
    st.session_state.chat_history
):

    with st.chat_message(msg["role"]):

        st.write(msg["content"])

        # -------------------------------------------------
        # Assistant Details
        # -------------------------------------------------

        if "details" in msg:

            with st.expander("🔍 جزئیات پاسخ"):
                render_details(msg["details"])

            # -------------------------------------------------
            # Suggested Questions
            # نکته: FollowupSuggester فعلاً به RAGGraph وصل نیست، پس این
            # کلید همیشه خالیه مگر اینکه بعداً وصلش کنیم.
            # -------------------------------------------------

            suggestions = (
                msg["details"].get("suggested_questions")
                or []
            )

            if (
                suggestions
                and msg_idx
                == len(st.session_state.chat_history) - 1
            ):

                st.markdown(
                    "**💡 سؤالات پیشنهادی:**"
                )

                cols = st.columns(
                    len(suggestions)
                )

                for col, suggestion in zip(
                    cols,
                    suggestions
                ):

                    with col:

                        if st.button(
                            suggestion,
                            key=f"suggestion_{msg_idx}_{suggestion}",
                            use_container_width=True
                        ):

                            st.session_state.pending_question = suggestion

                            st.rerun()


# =========================================================
# Chat Input
# =========================================================

typed_prompt = st.chat_input(
    "سوال خود را بپرسید..."
)

# سؤال می‌تواند از chat_input یا دکمه‌ی پیشنهادی بیاید
prompt = (
    st.session_state.pending_question
    or typed_prompt
)

# بعد از مصرف، پاک شود
st.session_state.pending_question = None


# =========================================================
# Process User Question
# =========================================================

if prompt:

    # -----------------------------------------------------
    # Add User Message
    # -----------------------------------------------------

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):

        st.write(prompt)

    # -----------------------------------------------------
    # Assistant
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        try:

            rag = st.session_state.rag_graph

            result = rag.run(
                prompt,
                session_id=st.session_state.session_id,
                top_k=top_k,
                max_retries=max_retries
            )

            # -------------------------------------------------
            # Extract Answer
            # -------------------------------------------------

            full_answer = result.get(
                "answer",
                "پاسخی تولید نشد."
            )

            # نمایش پاسخ
            st.write(full_answer)

            # -------------------------------------------------
            # Details
            # -------------------------------------------------

            with st.expander(
                "🔍 جزئیات پاسخ"
            ):
                render_details(result)

            # -------------------------------------------------
            # Save Assistant Message
            # -------------------------------------------------

            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": full_answer,
                    "details": result
                }
            )

            # Refresh UI
            st.rerun()

        except Exception as e:

            st.error(
                f"❌ خطا: {str(e)}"
            )