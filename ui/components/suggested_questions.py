# import html
# import streamlit as st


# def render_suggested_questions(
#     questions,
#     title="سوالات پیشنهادی"
# ):
#     """
#     Render suggested questions.

#     Can be displayed:
#     - In the empty chat state
#     - After an assistant response
#     """

#     if not questions:
#         return

#     items = []

#     for question in questions:

#         safe_question = html.escape(
#             str(question)
#         )

#         items.append(
#             f"""
#             <div class="suggested-question">
#                 <span class="suggested-question-icon">↗</span>
#                 <span>{safe_question}</span>
#             </div>
#             """
#         )

#     html_content = f"""
#     <div class="suggested-questions">

#         <div class="suggested-questions-title">
#             {html.escape(title)}
#         </div>

#         <div class="suggested-questions-list">
#             {''.join(items)}
#         </div>

#     </div>
#     """

#     st.html(html_content)

import html
import streamlit as st


def render_suggested_questions(
    questions,
    title="سوالات پیشنهادی"
):
    """
    Render suggested questions as clickable buttons.
    
    When a question is clicked, it will be stored in session_state
    and displayed in the input box.
    
    Returns:
        The selected question if a button is clicked, else None.
    """

    if not questions:
        return None

    selected = None
    
    # نمایش عنوان
    st.markdown(
        f"""
        <div class="suggested-questions-title">
            💡 {html.escape(title)}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # ایجاد ستون‌ها برای نمایش سوالات در ردیف
    cols = st.columns(min(len(questions), 3))  # حداکثر ۳ ستون
    
    for idx, question in enumerate(questions):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            # دکمه برای هر سوال
            if st.button(
                question,
                key=f"suggested_q_{idx}_{hash(question)}",
                use_container_width=True,
                type="secondary"
            ):
                selected = question
    
    return selected