import html
import streamlit as st


def render_suggested_questions(
    questions,
    title="سوالات پیشنهادی"
):
    """
    Render suggested questions.

    Can be displayed:
    - In the empty chat state
    - After an assistant response
    """

    if not questions:
        return

    items = []

    for question in questions:

        safe_question = html.escape(
            str(question)
        )

        items.append(
            f"""
            <div class="suggested-question">
                <span class="suggested-question-icon">↗</span>
                <span>{safe_question}</span>
            </div>
            """
        )

    html_content = f"""
    <div class="suggested-questions">

        <div class="suggested-questions-title">
            {html.escape(title)}
        </div>

        <div class="suggested-questions-list">
            {''.join(items)}
        </div>

    </div>
    """

    st.html(html_content)