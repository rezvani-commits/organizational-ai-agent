import streamlit as st


def render_input_box(default_value=None):
    """
    Render the chat input box.
    
    Args:
        default_value: مقدار پیش‌فرض برای نمایش در input box
    
    Returns:
        The user input text or None.
    """
    
    # غیرفعال کردن input در حین پردازش
    disabled = st.session_state.get("processing_message", False)
    
    placeholder = "در حال پردازش..." if disabled else "سوال خود را بپرسید..."
    
    # اگر مقدار پیش‌فرض وجود دارد، آن را به عنوان value تنظیم کن
    if default_value:
        # استفاده از text_input به جای chat_input برای نمایش مقدار پیش‌فرض
        user_input = st.text_input(
            label="پیام",
            placeholder=placeholder,
            value=default_value,
            disabled=disabled,
            key="user_input_box",
            label_visibility="collapsed"
        )
        
        # دکمه ارسال
        col1, col2 = st.columns([5, 1])
        with col1:
            # فقط placeholder برای نمایش
            pass
        with col2:
            if st.button("📤 ارسال", disabled=disabled, use_container_width=True):
                return user_input
        
        return None
    
    # حالت عادی با chat_input
    return st.chat_input(
        placeholder=placeholder,
        disabled=disabled
    )