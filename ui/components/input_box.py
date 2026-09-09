import streamlit as st


def render_input_box():
    """
    Render the main chat input.

    The visual appearance and positioning are handled
    centrally inside styles/style.py.
    """

    prompt = st.chat_input(
        "پیام خود را بنویسید..."
    )

    return prompt