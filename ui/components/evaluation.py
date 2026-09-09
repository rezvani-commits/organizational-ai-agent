import streamlit as st


def render_evaluation(scores):
    """
    Render response evaluation in a minimal GPT-like style.

    Evaluation appears as lightweight metadata
    below the assistant response instead of a separate card.
    """

    if not scores:
        return

    def percent(value):
        return int(float(value) * 100)

    relevance = percent(
        scores.get("relevance", 0)
    )

    completeness = percent(
        scores.get("completeness", 0)
    )

    faithfulness = percent(
        scores.get("faithfulness", 0)
    )

    html = f"""
    <div class="evaluation-section">

        <div class="evaluation-title">
            ارزیابی پاسخ
        </div>

        <div class="evaluation-items">

            <div class="evaluation-item">
                <span>ارتباط</span>
                <strong>{relevance}%</strong>
            </div>

            <div class="evaluation-item">
                <span>کامل بودن</span>
                <strong>{completeness}%</strong>
            </div>

            <div class="evaluation-item">
                <span>صحت</span>
                <strong>{faithfulness}%</strong>
            </div>

        </div>

    </div>
    """

    st.html(html)