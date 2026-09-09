import streamlit as st

from styles.style import load_css

from components.sidebar import render_sidebar

from components.chat_message import (
    render_user_message,
    render_ai_message
)

from components.input_box import render_input_box

from components.status import render_status

from components.citation import render_citations

from components.evaluation import render_evaluation

from components.suggested_questions import (
    render_suggested_questions
)

from data.mock_data import (
    get_mock_chats,
    get_mock_response
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# AUTHENTICATION CHECK
# =========================================================

if not st.session_state.get(
    "is_authenticated",
    False
):
    st.switch_page(
        "pages/login.py"
    )


# =========================================================
# LOAD CSS
# =========================================================

load_css()


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


if "user_menu_open" not in st.session_state:
    st.session_state.user_menu_open = False


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
# SIDEBAR
# =========================================================

render_sidebar(
    get_mock_chats()
)


# =========================================================
# PASSWORD CHANGE SUCCESS
# =========================================================

if st.session_state.pop(
    "password_change_success",
    False
):

    st.markdown(
        """
        <div class="password-success-toast">
            رمز عبور با موفقیت تغییر کرد.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CHAT AREA
# =========================================================

if not st.session_state.messages:

    # -----------------------------------------------------
    # WELCOME
    # -----------------------------------------------------

    st.html(
        """
        <div class="chat-welcome">

            <h1>
                سلام 👋
            </h1>

            <h3>
                سوال خود را از دستیار هوشمند بپرسید
            </h3>

            <p>
                پاسخ‌ها بر اساس اسناد سازمانی تولید می‌شوند.
            </p>

        </div>
        """
    )


    # -----------------------------------------------------
    # INITIAL SUGGESTED QUESTIONS
    # -----------------------------------------------------

    selected_question = render_suggested_questions(
        [
            "شرایط دریافت مجوز احداث نیروگاه چیست؟",
            "مدارک لازم برای احداث نیروگاه چیست؟",
            "قوانین اتصال نیروگاه به شبکه چیست؟"
        ]
    )


    # -----------------------------------------------------
    # SEND SELECTED QUESTION
    # -----------------------------------------------------

    if selected_question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": selected_question
            }
        )

        st.session_state.processing_message = True

        st.session_state.processing_started = True

        st.session_state.scroll_to_bottom = True

        st.rerun()


# =========================================================
# CHAT HISTORY
# =========================================================

else:

    selected_question = None

    for message in st.session_state.messages:

        # -------------------------------------------------
        # USER MESSAGE
        # -------------------------------------------------

        if message["role"] == "user":

            render_user_message(
                message["content"]
            )


        # -------------------------------------------------
        # ASSISTANT MESSAGE
        # -------------------------------------------------

        elif message["role"] == "assistant":

            render_ai_message(
                message["content"]
            )

            render_citations(
                message.get("sources")
            )

            render_evaluation(
                message.get("scores")
            )

            # -------------------------------------------------
            # SUGGESTED QUESTIONS
            # -------------------------------------------------

            question = render_suggested_questions(
                message.get("suggestions", [])
            )

            if question:

                selected_question = question


    # -----------------------------------------------------
    # SEND SELECTED QUESTION
    # -----------------------------------------------------

    if selected_question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": selected_question
            }
        )

        st.session_state.processing_message = True

        st.session_state.processing_started = True

        st.session_state.scroll_to_bottom = True

        st.rerun()


# =========================================================
# PROCESSING
# =========================================================

if st.session_state.processing_message:

    render_status()


    # -----------------------------------------------------
    # MOCK BACKEND
    # -----------------------------------------------------

    response = get_mock_response()


    # -----------------------------------------------------
    # ADD ASSISTANT RESPONSE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",

            "content": response["answer"],

            "sources": response["sources"],

            "scores": response["scores"],

            "suggestions": response.get(
                "suggestions",
                []
            )
        }
    )


    # -----------------------------------------------------
    # PROCESSING FINISHED
    # -----------------------------------------------------

    st.session_state.processing_message = False

    st.session_state.processing_started = False

    st.session_state.scroll_to_bottom = True


    # -----------------------------------------------------
    # RERUN
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# INPUT
# =========================================================

user_input = render_input_box()


# =========================================================
# NEW USER MESSAGE
# =========================================================

if user_input:

    user_input = user_input.strip()

    if user_input:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        st.session_state.processing_message = True

        st.session_state.processing_started = True

        st.session_state.scroll_to_bottom = True

        st.rerun()


# =========================================================
# AUTO SCROLL
# =========================================================

if st.session_state.pop(
    "scroll_to_bottom",
    False
):

    st.markdown(
        """
        <script>

        setTimeout(function() {

            const container =
                document.querySelector(
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