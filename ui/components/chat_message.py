import streamlit as st


def render_user_message(message):

    html = f"""
    <div style="
        display:flex;
        justify-content:flex-start;
        direction:rtl;
        margin:12px 0;
    ">

        <div style="
            background-color:#3B82F6;
            color:white;
            padding:10px 16px;
            border-radius:14px;
            max-width:55%;
            direction:rtl;
            text-align:center;
        ">
            {message}
        </div>

    </div>
    """

    st.html(html)


def render_ai_message(answer):

    html = f"""
    <div style="
        display:flex;
        justify-content:flex-end;
        width:100%;
        direction:rtl;
        margin:5px 0;
    ">

        <div style="
            background:transparent;
            color:white;
            padding:5px;
            border:none;
            border-radius:0;
            box-shadow:none;
            max-width:100%;
            width:100%;
            direction:rtl;
            text-align:right;
        ">

            <div style="
                color:#3B82F6;
                font-weight:600;
                margin-bottom:10px;
            ">
                 دستیار هوشمند
            </div>

            <div style="
                line-height:1.8;
            ">
                {answer}
            </div>

        </div>

    </div>
    """

    st.html(html)