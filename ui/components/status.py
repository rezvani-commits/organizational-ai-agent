import streamlit as st
import time


def render_status():
    """
    Render a minimal GPT-like processing status.

    The status appears naturally inside the conversation
    instead of looking like a separate card.
    """

    steps = [
        "جستجو در اسناد",
        "بازیابی اطلاعات مرتبط",
        "تولید پاسخ",
        "ارزیابی پاسخ"
    ]

    status_placeholder = st.empty()

    for current_step in range(len(steps)):

        html = """
        <div class="chat-status">

            <div class="chat-status-title">
                <span class="status-spinner"></span>
                <span>در حال پردازش...</span>
            </div>

            <div class="chat-status-steps">
        """

        for index, step in enumerate(steps):

            if index < current_step:

                icon = """
                <span class="status-check">
                    ✓
                </span>
                """

                text_color = "#AFAFAF"

            elif index == current_step:

                icon = """
                <span class="status-spinner-small"></span>
                """

                text_color = "#FFFFFF"

            else:

                icon = """
                <span class="status-pending"></span>
                """

                text_color = "#666666"

            html += f"""
                <div
                    class="chat-status-step"
                    style="color:{text_color};"
                >
                    {icon}

                    <span>
                        {step}
                    </span>
                </div>
            """

        html += """
            </div>

        </div>
        """

        status_placeholder.html(html)

        time.sleep(0.7)

    # -----------------------------------------------------
    # Final state
    # -----------------------------------------------------

    final_html = """
    <div class="chat-status chat-status-final">

        <div class="chat-status-title">
            <span class="status-check">
                ✓
            </span>

            <span>
                پردازش کامل شد
            </span>
        </div>

    </div>
    """

    status_placeholder.html(final_html)