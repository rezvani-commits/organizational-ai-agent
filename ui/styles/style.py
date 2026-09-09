import streamlit as st


def load_css(show_sidebar=True):
    """
    Global UI styling.

    show_sidebar=True  -> Main application
    show_sidebar=False -> Login page
    """

    if show_sidebar:
        sidebar_css = """
        /* =========================================================
           SIDEBAR
           ========================================================= */

        section[data-testid="stSidebar"] {
            background-color: #2F2F2F !important;

            transform: none !important;
            visibility: visible !important;

            min-width: 270px !important;
            max-width: 500px !important;
        }

        section[data-testid="stSidebar"] * {
            direction: rtl;
        }

        section[data-testid="stSidebar"] button {
            border-radius: 10px !important;
        }


        /* =========================================================
           DISABLE SIDEBAR COLLAPSE
           ========================================================= */

        [data-testid="collapsedControl"] {
            display: none !important;
        }

        section[data-testid="stSidebar"]
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        """

    else:
        sidebar_css = """
        /* =========================================================
           HIDE SIDEBAR ON LOGIN
           ========================================================= */

        section[data-testid="stSidebar"] {
            display: none !important;
        }

        [data-testid="collapsedControl"] {
            display: none !important;
        }
        """

    st.markdown(
        f"""
        <style>

        /* =========================================================
           FONT
           ========================================================= */

        @import url(
            'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&display=swap'
        );


        /* =========================================================
           GLOBAL
           ========================================================= */

        html,
        body,
        [class*="css"] {{
            font-family: 'Vazirmatn', sans-serif !important;
            direction: rtl;
        }}

        .stApp {{
            background-color: #212121;
            color: #FFFFFF;
        }}


        /* =========================================================
           HIDE STREAMLIT DEFAULT UI
           ========================================================= */

        #MainMenu {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}


        /* =========================================================
           SIDEBAR MODE
           ========================================================= */

        {sidebar_css}


        /* =========================================================
           GENERAL BUTTONS
           ========================================================= */

        .stButton > button {{
            background-color: #3B82F6 !important;
            color: #FFFFFF !important;

            border: none !important;
            border-radius: 12px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            transition:
                background-color 0.15s ease,
                transform 0.15s ease,
                box-shadow 0.15s ease !important;
        }}

        .stButton > button:hover {{
            background-color: #2563EB !important;
        }}


        /* =========================================================
           TEXTAREA
           ========================================================= */

        textarea {{
            background-color: #2F2F2F !important;
            color: #FFFFFF !important;

            direction: rtl !important;

            font-family: 'Vazirmatn', sans-serif !important;
        }}


        /* =========================================================
           CHAT INPUT
           ========================================================= */

        [data-testid="stBottom"] {{
            background: linear-gradient(
                to top,
                #212121 70%,
                rgba(33, 33, 33, 0)
            ) !important;

            border: none !important;
        }}

        [data-testid="stBottom"] > div {{
            background: transparent !important;
        }}

        [data-testid="stChatInput"] {{
            background-color: #2F2F2F !important;

            border: 1px solid #454545 !important;

            border-radius: 18px !important;

            overflow: hidden !important;

            box-shadow:
                0 4px 20px rgba(0, 0, 0, 0.18) !important;

            transition:
                border-color 0.15s ease,
                box-shadow 0.15s ease !important;
        }}

        [data-testid="stChatInput"]:hover {{
            border-color: #555555 !important;
        }}

        [data-testid="stChatInput"]:focus-within {{
            border: 1px solid #3B82F6 !important;

            box-shadow:
                0 0 0 1px rgba(59, 130, 246, 0.12),
                0 6px 24px rgba(0, 0, 0, 0.22) !important;
        }}

        [data-testid="stChatInput"] > div {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }}

        [data-testid="stChatInput"] textarea {{
            background-color: transparent !important;

            color: #FFFFFF !important;

            direction: rtl !important;
            text-align: right !important;

            font-family: 'Vazirmatn', sans-serif !important;

            border: none !important;
            outline: none !important;
            box-shadow: none !important;

            padding-right: 14px !important;
        }}

        [data-testid="stChatInput"] textarea::placeholder {{
            color: #858585 !important;

            font-family: 'Vazirmatn', sans-serif !important;
        }}


        /* =========================================================
           CHAT SEND BUTTON
           ========================================================= */

        [data-testid="stChatInput"] button {{
            background-color: #3B82F6 !important;

            color: #FFFFFF !important;

            border: none !important;

            border-radius: 10px !important;

            transition:
                background-color 0.15s ease,
                transform 0.15s ease !important;
        }}

        [data-testid="stChatInput"] button:hover {{
            background-color: #2563EB !important;

            transform: translateY(-1px);
        }}


        /* =========================================================
           CHAT HISTORY
           ========================================================= */

        .chat-item {{
            direction: rtl;
            text-align: right;

            color: #D4D4D4;

            font-size: 14px;
            font-weight: 400;

            padding: 9px 10px;

            margin: 1px 0;

            border-radius: 8px;

            background: transparent;

            cursor: pointer;

            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;

            transition:
                background-color 0.12s ease,
                color 0.12s ease;
        }}

        .chat-item:hover {{
            background-color: #3A3A3A;
            color: #FFFFFF;
        }}


        /* =========================================================
           USER MESSAGE
           ========================================================= */

        .user-message-row {{
            width: 100%;

            display: flex;

            justify-content: flex-start;

            direction: rtl;

            margin: 18px 0;

            box-sizing: border-box;
        }}

        .user-message {{
            background-color: #3B82F6;

            color: #FFFFFF;

            padding: 10px 15px;

            border-radius: 16px 16px 4px 16px;

            max-width: 68%;

            font-size: 15px;

            line-height: 1.8;

            text-align: right;

            direction: rtl;

            word-break: break-word;

            box-shadow:
                0 2px 8px rgba(0, 0, 0, 0.12);
        }}


        /* =========================================================
           AI MESSAGE — NO CARD
           ========================================================= */

        .stElement:has(.ai-message-row),
        .stMarkdown:has(.ai-message-row),
        [data-testid="stElementContainer"]:has(.ai-message-row) {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }}

        .ai-message-row {{
            width: 100% !important;

            display: flex !important;

            justify-content: flex-end !important;

            direction: rtl !important;

            margin: 24px 0 10px 0 !important;

            padding: 0 !important;

            background: transparent !important;

            border: none !important;

            box-shadow: none !important;

            box-sizing: border-box !important;
        }}

        .ai-message {{
            width: 100% !important;

            max-width: 850px !important;

            background: transparent !important;

            border: none !important;

            outline: none !important;

            box-shadow: none !important;

            padding: 0 !important;

            margin: 0 !important;

            color: #FFFFFF !important;

            direction: rtl !important;

            text-align: right !important;

            word-break: break-word !important;
        }}

        .ai-title {{
            display: flex !important;

            align-items: center !important;

            justify-content: flex-start !important;

            gap: 8px !important;

            color: #FFFFFF !important;

            font-size: 15px !important;

            font-weight: 600 !important;

            margin-bottom: 10px !important;

            direction: rtl !important;

            background: transparent !important;

            border: none !important;

            box-shadow: none !important;
        }}

        .ai-icon {{
            display: inline-flex !important;

            align-items: center !important;

            justify-content: center !important;

            width: 28px !important;

            height: 28px !important;

            border-radius: 9px !important;

            background-color: rgba(59, 130, 246, 0.14) !important;

            font-size: 15px !important;

            flex-shrink: 0 !important;
        }}

        .ai-content {{
            color: #E8E8E8 !important;

            font-size: 15px !important;

            line-height: 2 !important;

            direction: rtl !important;

            text-align: right !important;

            padding-right: 36px !important;

            padding-left: 0 !important;

            background: transparent !important;

            border: none !important;

            outline: none !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           CITATIONS
           ========================================================= */

        .citations-section {{
            width: 100%;

            max-width: 850px;

            margin: 6px 0 10px auto;

            padding-right: 36px;

            direction: rtl;

            text-align: right;

            box-sizing: border-box;
        }}

        .citations-title {{
            color: #9A9A9A;

            font-size: 14px;

            font-weight: 500;

            margin-bottom: 8px;
        }}

        .citations-list {{
            display: flex;

            flex-direction: column;

            gap: 5px;
        }}

        .citation-item {{
            display: flex;

            align-items: center;

            gap: 8px;

            width: fit-content;

            max-width: 100%;

            color: #BDBDBD;

            font-size: 14px;

            line-height: 1.8;

            padding: 2px 0;

            direction: rtl;
        }}

        .citation-icon {{
            opacity: 0.8;

            font-size: 14px;
        }}

        .citation-name {{
            color: #C8C8C8;

            overflow: hidden;

            text-overflow: ellipsis;

            white-space: nowrap;
        }}

        .citation-page {{
            color: #858585;

            white-space: nowrap;
        }}


        /* =========================================================
           EVALUATION
           ========================================================= */

        .evaluation-section {{
            width: 100%;

            max-width: 850px;

            margin: 5px 0 26px auto;

            padding-right: 36px;

            direction: rtl;

            box-sizing: border-box;
        }}

        .evaluation-title {{
            color: #858585;

            font-size: 14px;

            font-weight: 500;

            margin-bottom: 7px;
        }}

        .evaluation-items {{
            display: flex;

            align-items: center;

            justify-content: flex-start;

            gap: 18px;

            flex-wrap: wrap;
        }}

        .evaluation-item {{
            display: flex;

            align-items: center;

            gap: 6px;

            color: #8F8F8F;

            font-size: 14px;
        }}

        .evaluation-item strong {{
            color: #BDBDBD;

            font-size: 14px;

            font-weight: 500;
        }}


        /* =========================================================
           EMPTY CHAT AREA
           ========================================================= */

        .chat-welcome {{
            width: min(850px, calc(100vw - 80px));

            margin: 0 auto;

            direction: rtl;

            text-align: center;

            padding-top: 22vh;

            box-sizing: border-box;
        }}

        .chat-welcome h1 {{
            color: #FFFFFF;

            font-size: 32px;

            font-weight: 600;

            margin: 0 0 12px 0;
        }}

        .chat-welcome h3 {{
            color: #E8E8E8;

            font-size: 20px;

            font-weight: 500;

            margin: 0 0 8px 0;
        }}

        .chat-welcome p {{
            color: #8E8E8E;

            font-size: 14px;

            line-height: 1.8;

            margin: 0;
        }}


        /* =========================================================
           SUGGESTED QUESTIONS
           ========================================================= */

        .suggested-questions {{
            width: min(850px, calc(100vw - 80px));

            margin: 32px auto 10px auto;

            direction: rtl;

            text-align: right;

            box-sizing: border-box;
        }}

        .suggested-questions-title {{
            color: #8E8E8E;

            font-size: 14px;

            font-weight: 500;

            margin-bottom: 10px;

            text-align: right;
        }}

        .suggested-questions-list {{
            display: flex;

            flex-direction: column;

            gap: 6px;
        }}

        .suggested-question {{
            display: flex;

            align-items: center;

            gap: 8px;

            width: 100%;

            box-sizing: border-box;

            color: #C8C8C8;

            background: #292929;

            border: 1px solid #353535;

            border-radius: 11px;

            padding: 10px 13px;

            font-size: 13px;

            line-height: 1.7;

            direction: rtl;

            transition:
                background-color 0.15s ease,
                border-color 0.15s ease,
                color 0.15s ease;
        }}

        .suggested-question:hover {{
            background-color: #303030;

            border-color: #454545;

            color: #FFFFFF;
        }}

        .suggested-question-icon {{
            color: #3B82F6;

            font-size: 15px;

            flex-shrink: 0;
        }}


        /* =========================================================
           PROCESSING STATUS
           ========================================================= */

        .chat-status {{
            width: 100%;

            max-width: 850px;

            margin: 16px 0 20px auto;

            direction: rtl;

            text-align: right;

            color: #AFAFAF;
        }}

        .chat-status-title {{
            display: flex;

            align-items: center;

            gap: 8px;

            color: #AFAFAF;

            font-size: 13px;

            font-weight: 500;

            margin-bottom: 9px;

            direction: rtl;
        }}

        .chat-status-steps {{
            display: flex;

            flex-direction: column;

            gap: 6px;

            padding-right: 4px;
        }}

        .chat-status-step {{
            display: flex;

            align-items: center;

            gap: 8px;

            font-size: 12px;

            line-height: 1.6;

            direction: rtl;
        }}

        .status-spinner {{
            width: 13px;

            height: 13px;

            border: 2px solid #4A4A4A;

            border-top-color: #3B82F6;

            border-radius: 50%;

            animation:
                chat-spin 0.8s linear infinite;

            flex-shrink: 0;
        }}

        .status-spinner-small {{
            width: 10px;

            height: 10px;

            border: 1.5px solid #4A4A4A;

            border-top-color: #3B82F6;

            border-radius: 50%;

            animation:
                chat-spin 0.8s linear infinite;

            flex-shrink: 0;
        }}

        .status-check {{
            display: inline-flex;

            align-items: center;

            justify-content: center;

            width: 14px;

            height: 14px;

            color: #3B82F6;

            font-size: 12px;

            font-weight: 700;

            flex-shrink: 0;
        }}

        .status-pending {{
            width: 6px;

            height: 6px;

            background-color: #555555;

            border-radius: 50%;

            margin-right: 4px;

            margin-left: 4px;

            flex-shrink: 0;
        }}

        .chat-status-final {{
            margin-top: 10px;

            margin-bottom: 20px;
        }}

        .chat-status-final .chat-status-title {{
            color: #8E8E8E;

            margin-bottom: 0;
        }}

        @keyframes chat-spin {{

            from {{
                transform: rotate(0deg);
            }}

            to {{
                transform: rotate(360deg);
            }}

        }}


        /* =========================================================
           LOGIN HEADER
           ========================================================= */

        .login-header {{
            width: 100%;

            text-align: center;

            direction: rtl;

            margin-top: 5vh;

            margin-bottom: 4vh;
        }}


        /* =========================================================
           LOGIN LOGO
           ========================================================= */

        .login-logo {{
            width: 72px;

            height: 72px;

            margin: 0 auto 24px auto;

            display: flex;

            align-items: center;

            justify-content: center;

            background-color: #2F2F2F;

            border-radius: 20px;

            font-size: 34px;
        }}


        /* =========================================================
           LOGIN TITLE
           ========================================================= */

        .login-title {{
            color: #FFFFFF;

            font-size: 36px;

            font-weight: 600;

            margin-bottom: 12px;
        }}


        /* =========================================================
           LOGIN SUBTITLE
           ========================================================= */

        .login-subtitle {{
            color: #AFAFAF;

            font-size: 18px;

            line-height: 1.8;
        }}


        /* =========================================================
           LOGIN FORM
           ========================================================= */

        [data-testid="stForm"] {{
            width: 100% !important;

            background: transparent !important;

            border: none !important;

            padding: 0 !important;

            box-shadow: none !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"] {{

            width: 100% !important;

            margin-bottom: 24px !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"] > div {{

            position: relative !important;

            width: 100% !important;

            background: transparent !important;

            border: none !important;

            outline: none !important;

            box-shadow: none !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"] > div > div {{

            position: relative !important;

            background: transparent !important;

            border: none !important;

            outline: none !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           LOGIN INPUT
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stTextInput"] input {{

            box-sizing: border-box !important;

            width: 100% !important;

            height: 62px !important;

            background-color: #2F2F2F !important;

            color: #FFFFFF !important;

            direction: rtl !important;

            text-align: right !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 18px !important;

            border: 2px solid #4A4A4A !important;

            border-radius: 16px !important;

            padding: 0 20px !important;

            outline: none !important;

            box-shadow: none !important;

            transition:
                border-color 0.15s ease,
                box-shadow 0.15s ease !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"] input:focus {{

            background-color: #2F2F2F !important;

            color: #FFFFFF !important;

            border: 2px solid #3B82F6 !important;

            outline: none !important;

            box-shadow:
                0 0 0 1px #3B82F6 !important;
        }}


        /* =========================================================
           REMOVE STREAMLIT FOCUS
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stTextInput"]:focus-within {{

            border: none !important;

            outline: none !important;

            box-shadow: none !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"]:focus-within > div,

        [data-testid="stForm"]
        [data-testid="stTextInput"]:focus-within > div > div {{

            border: none !important;

            outline: none !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           PLACEHOLDER
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stTextInput"]
        input::placeholder {{

            color: #888888 !important;

            opacity: 1 !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 15px !important;

            direction: rtl !important;

            text-align: right !important;
        }}


        /* =========================================================
           LOGIN LABEL
           ========================================================= */

        [data-testid="stForm"] label {{

            color: #D4D4D4 !important;

            font-size: 20px !important;

            font-weight: 600 !important;

            direction: rtl !important;

            text-align: right !important;

            margin-bottom: 12px !important;
        }}


        /* =========================================================
           PASSWORD INPUT
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stTextInput"]
        input[type="password"],

        [data-testid="stForm"]
        [data-testid="stTextInput"]
        input[type="text"] {{

            padding-left: 52px !important;
        }}


        /* =========================================================
           PASSWORD VISIBILITY
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stTextInput"]
        button {{

            position: absolute !important;

            left: 8px !important;

            right: auto !important;

            top: 50% !important;

            transform: translateY(-50%) !important;

            width: 40px !important;

            height: 40px !important;

            margin: 0 !important;

            padding: 0 !important;

            background: transparent !important;

            color: #888888 !important;

            border: none !important;

            border-radius: 10px !important;

            outline: none !important;

            box-shadow: none !important;

            z-index: 10 !important;
        }}

        [data-testid="stForm"]
        [data-testid="stTextInput"]
        button:hover {{

            background: transparent !important;

            color: #FFFFFF !important;

            border: none !important;

            box-shadow: none !important;

            transform: translateY(-50%) !important;
        }}


        /* =========================================================
           AUTOFILL
           ========================================================= */

        [data-testid="stForm"] input:-webkit-autofill,

        [data-testid="stForm"] input:-webkit-autofill:hover,

        [data-testid="stForm"] input:-webkit-autofill:focus,

        [data-testid="stForm"] input:-webkit-autofill:active {{

            -webkit-box-shadow:
                0 0 0 1000px #2F2F2F inset !important;

            -webkit-text-fill-color: #FFFFFF !important;

            background-color: #2F2F2F !important;

            border: 2px solid #4A4A4A !important;
        }}


        /* =========================================================
           LOGIN BUTTON
           ========================================================= */

        [data-testid="stForm"]
        [data-testid="stFormSubmitButton"] {{

            width: 60% !important;

            display: flex !important;

            justify-content: center !important;

            margin: 0 auto !important;

            padding-top: 10px !important;
        }}

        [data-testid="stForm"]
        [data-testid="stFormSubmitButton"] button {{

            width: 100% !important;

            height: 48px !important;

            margin: 0 !important;

            background-color: #3B82F6 !important;

            color: #FFFFFF !important;

            border: none !important;

            border-radius: 16px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 18px !important;

            font-weight: 700 !important;

            box-shadow:
                0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }}

        [data-testid="stForm"]
        [data-testid="stFormSubmitButton"] button:hover {{

            background-color: #2563EB !important;

            color: #FFFFFF !important;

            box-shadow:
                0 6px 16px rgba(59, 130, 246, 0.4) !important;

            transform: translateY(-2px) !important;
        }}


        /* =========================================================
           LOGIN ERROR
           ========================================================= */

        [data-testid="stForm"] ~ div
        [data-testid="stAlert"] {{

            margin-top: 18px !important;

            border-radius: 14px !important;

            text-align: center !important;

            direction: rtl !important;
        }}


        /* =========================================================
           SIDEBAR LAYOUT
           ========================================================= */

        section[data-testid="stSidebar"] > div:first-child {{

            position: relative !important;

            height: 100vh !important;

            overflow: hidden !important;
        }}


        /* =========================================================
           RECENT CONVERSATIONS TITLE
           ========================================================= */

        .sidebar-history-title {{

            direction: rtl;

            text-align: right;

            color: #FFFFFF;

            font-size: 17px;

            font-weight: 600;

            margin-bottom: 8px;

            padding-right: 8px;
        }}


        /* =========================================================
           RECENT CONVERSATIONS CONTAINER
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-recent_history {{

            height: calc(100vh - 185px) !important;

            max-height: calc(100vh - 185px) !important;

            overflow-y: auto !important;

            overflow-x: hidden !important;

            padding-right: 2px !important;

            padding-left: 4px !important;

            padding-bottom: 100px !important;

            margin-bottom: 0 !important;

            box-sizing: border-box !important;
        }}


        /* =========================================================
           RECENT CONVERSATIONS SCROLLBAR
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-recent_history::-webkit-scrollbar {{

            width: 5px;
        }}

        section[data-testid="stSidebar"]
        .st-key-recent_history::-webkit-scrollbar-track {{

            background: transparent;
        }}

        section[data-testid="stSidebar"]
        .st-key-recent_history::-webkit-scrollbar-thumb {{

            background: #555555;

            border-radius: 10px;
        }}

        section[data-testid="stSidebar"]
        .st-key-recent_history::-webkit-scrollbar-thumb:hover {{

            background: #666666;
        }}


        /* =========================================================
           CHAT ITEMS — GPT STYLE
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-recent_history
        .chat-item {{

            background: transparent !important;

            border: none !important;

            border-radius: 8px !important;

            padding: 9px 10px !important;

            margin: 1px 0 !important;

            direction: rtl !important;

            text-align: right !important;

            color: #D4D4D4 !important;

            font-size: 14px !important;

            font-weight: 400 !important;

            cursor: pointer !important;

            white-space: nowrap !important;

            overflow: hidden !important;

            text-overflow: ellipsis !important;

            transition:
                background-color 0.12s ease,
                color 0.12s ease !important;
        }}

        section[data-testid="stSidebar"]
        .st-key-recent_history
        .chat-item:hover {{

            background-color: #3A3A3A !important;

            color: #FFFFFF !important;
        }}


        /* =========================================================
           USER SECTION
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section {{

            position: absolute !important;

            left: 0 !important;

            right: 0 !important;

            bottom: 0 !important;

            width: 100% !important;

            box-sizing: border-box !important;

            background-color: #2F2F2F !important;

            padding: 0 16px 12px 16px !important;

            z-index: 100 !important;

            direction: rtl;
        }}

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section
        hr {{

            margin-top: 6px !important;

            margin-bottom: 6px !important;
        }}


        /* =========================================================
           USER NAME BUTTON
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section
        .stButton > button {{

            background: transparent !important;

            color: #E8E8E8 !important;

            border: none !important;

            box-shadow: none !important;

            border-radius: 10px !important;

            direction: rtl !important;

            text-align: right !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;

            font-weight: 500 !important;

            padding: 6px !important;

            margin: 0 !important;

            min-height: 0 !important;
        }}

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section
        .stButton > button:hover {{

            background-color: #3A3A3A !important;

            color: #FFFFFF !important;

            border: none !important;

            box-shadow: none !important;

            transform: none !important;
        }}


        /* =========================================================
           USER DEPARTMENT
           ========================================================= */

        .sidebar-user-department {{

            direction: rtl;

            text-align: center;

            color: #8E8E8E;

            margin-bottom: 20px;

            font-size: 20px;

            padding:
                0
                0px
                0px
                0px;
        }}


        /* =========================================================
           CHANGE PASSWORD MODAL
           ========================================================= */

        [data-testid="stDialog"] {{

            direction: rtl !important;

            border-radius: 18px !important;

            overflow: hidden !important;
        }}


        /* =========================================================
           MODAL CONTENT
           ========================================================= */

        [data-testid="stDialog"] > div {{

            padding: 16px 24px 14px 24px !important;

            direction: rtl !important;
        }}


        /* =========================================================
           MODAL TITLE
           ========================================================= */

        [data-testid="stDialog"] h2 {{

            color: #FFFFFF !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 20px !important;

            font-weight: 600 !important;

            text-align: center !important;

            margin-top: 0 !important;

            margin-bottom: 11px !important;
        }}


        /* =========================================================
           MODAL INPUTS
           ========================================================= */

        [data-testid="stDialog"]
        [data-testid="stTextInput"] {{

            margin-bottom: 5px !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stTextInput"] label {{

            color: #D4D4D4 !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 13px !important;

            font-weight: 500 !important;

            direction: rtl !important;

            text-align: right !important;

            margin-bottom: 3px !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stTextInput"] input {{

            box-sizing: border-box !important;

            width: 100% !important;

            height: 43px !important;

            background-color: #2F2F2F !important;

            color: #FFFFFF !important;

            direction: rtl !important;

            text-align: right !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 13px !important;

            border: 1px solid #4A4A4A !important;

            border-radius: 11px !important;

            padding: 0 13px !important;

            outline: none !important;

            box-shadow: none !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stTextInput"] input:focus {{

            border: 1px solid #3B82F6 !important;

            outline: none !important;

            box-shadow:
                0 0 0 1px #3B82F6 !important;
        }}


        /* =========================================================
           PASSWORD EYE
           ========================================================= */

        [data-testid="stDialog"]
        [data-testid="stTextInput"] button {{

            border-radius: 8px !important;

            background: transparent !important;

            color: #888888 !important;

            border: none !important;

            box-shadow: none !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stTextInput"] button:hover {{

            background: transparent !important;

            color: #FFFFFF !important;
        }}


        /* =========================================================
           MODAL BUTTONS
           ========================================================= */

        [data-testid="stDialog"]
        .stButton > button {{

            height: 40px !important;

            border-radius: 11px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 13px !important;

            font-weight: 500 !important;

            margin-top: 0 !important;

            transition:
                background-color 0.15s ease,
                border-color 0.15s ease,
                box-shadow 0.15s ease !important;
        }}


        /* =========================================================
           SAVE
           ========================================================= */

        [data-testid="stDialog"]
        .stColumn:first-child
        .stButton > button {{

            background-color: #3B82F6 !important;

            color: #FFFFFF !important;

            border: 1px solid #3B82F6 !important;

            box-shadow:
                0 2px 8px rgba(59, 130, 246, 0.18) !important;
        }}

        [data-testid="stDialog"]
        .stColumn:first-child
        .stButton > button:hover {{

            background-color: #2563EB !important;

            border-color: #2563EB !important;

            box-shadow:
                0 3px 10px rgba(59, 130, 246, 0.28) !important;

            transform: none !important;
        }}


        /* =========================================================
           CANCEL
           ========================================================= */

        [data-testid="stDialog"]
        .stColumn:nth-child(2)
        .stButton > button {{

            background-color: #3A3A3A !important;

            color: #D4D4D4 !important;

            border: 1px solid #4A4A4A !important;

            box-shadow: none !important;
        }}

        [data-testid="stDialog"]
        .stColumn:nth-child(2)
        .stButton > button:hover {{

            background-color: #454545 !important;

            color: #FFFFFF !important;

            border-color: #555555 !important;

            box-shadow: none !important;

            transform: none !important;
        }}


        /* =========================================================
           MODAL ALERTS
           ========================================================= */

        [data-testid="stDialog"]
        [data-testid="stAlert"] {{

            width: 100% !important;

            box-sizing: border-box !important;

            margin: 5px auto 7px auto !important;

            padding: 7px 10px !important;

            border-radius: 11px !important;

            direction: rtl !important;

            text-align: center !important;

            display: flex !important;

            justify-content: center !important;

            align-items: center !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stAlert"] > div {{

            width: 100% !important;

            display: flex !important;

            justify-content: center !important;

            align-items: center !important;

            text-align: center !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stAlert"]
        [data-testid="stMarkdownContainer"] {{

            width: 100% !important;

            display: flex !important;

            justify-content: center !important;

            align-items: center !important;

            text-align: center !important;
        }}

        [data-testid="stDialog"]
        [data-testid="stAlert"] p {{

            width: 100% !important;

            text-align: center !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 12px !important;

            line-height: 1.5 !important;

            margin: 0 !important;
        }}


        /* =========================================================
           LOGOUT BUTTON
           ========================================================= */

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section
        .st-key-user_logout_button
        button {{

            background-color: rgba(190, 45, 55, 0.15) !important;

            color: #FF7B84 !important;

            border: 1px solid rgba(255, 80, 90, 0.28) !important;

            box-shadow:
                0 0 12px rgba(220, 50, 60, 0.10),
                inset 0 0 10px rgba(220, 50, 60, 0.04) !important;
        }}

        section[data-testid="stSidebar"]
        .st-key-sidebar_user_section
        .st-key-user_logout_button
        button:hover {{

            background-color: rgba(200, 45, 55, 0.24) !important;

            color: #FF9AA1 !important;

            border-color: rgba(255, 80, 90, 0.45) !important;

            box-shadow:
                0 0 18px rgba(220, 50, 60, 0.22),
                inset 0 0 14px rgba(220, 50, 60, 0.08) !important;

            transform: none !important;
        }}


        /* =========================================================
           PASSWORD SUCCESS TOAST
           ========================================================= */

        .password-success-toast {{

            position: fixed;

            top: 24px;

            right: 50%;

            transform: translateX(50%);

            z-index: 999999;

            background: rgba(34, 197, 94, 0.18);

            color: #86EFAC;

            border: 1px solid rgba(34, 197, 94, 0.45);

            padding: 11px 22px;

            border-radius: 12px;

            font-family: "Vazirmatn", sans-serif;

            font-size: 13px;

            font-weight: 500;

            box-shadow:
                0 8px 30px rgba(0, 0, 0, 0.35),
                0 0 18px rgba(34, 197, 94, 0.08);

            direction: rtl;

            text-align: center;

            pointer-events: none;
        }}


        /* =========================================================
           RESPONSIVE — GENERAL
           ========================================================= */

        @media (max-width: 700px) {{

            .login-header {{

                margin-top: 4vh;

                margin-bottom: 3vh;

                padding: 0 20px;
            }}

            .login-logo {{

                width: 64px;

                height: 64px;

                font-size: 30px;

                margin-bottom: 20px;
            }}

            .login-title {{

                font-size: 30px;
            }}

            .login-subtitle {{

                font-size: 16px;
            }}

            [data-testid="stForm"] label {{

                font-size: 17px !important;
            }}

            [data-testid="stForm"]
            [data-testid="stTextInput"]
            input {{

                height: 54px !important;

                font-size: 16px !important;
            }}

            [data-testid="stForm"]
            [data-testid="stTextInput"]
            input[type="password"],

            [data-testid="stForm"]
            [data-testid="stTextInput"]
            input[type="text"] {{

                padding-left: 48px !important;
            }}

            [data-testid="stForm"]
            [data-testid="stFormSubmitButton"] {{

                width: 70% !important;
            }}

            [data-testid="stForm"]
            [data-testid="stFormSubmitButton"]
            button {{

                height: 44px !important;

                font-size: 16px !important;
            }}


            /* =====================================================
               COMPACT MODAL
               ===================================================== */

            [data-testid="stDialog"] > div {{

                padding: 14px 16px 12px 16px !important;
            }}

            [data-testid="stDialog"] h2 {{

                font-size: 18px !important;

                margin-bottom: 9px !important;
            }}

            [data-testid="stDialog"]
            [data-testid="stTextInput"] {{

                margin-bottom: 4px !important;
            }}

            [data-testid="stDialog"]
            [data-testid="stTextInput"] input {{

                height: 41px !important;
            }}

            [data-testid="stDialog"]
            .stButton > button {{

                height: 39px !important;
            }}


            /* =====================================================
               CHAT MOBILE
               ===================================================== */

            .chat-welcome {{

                width: calc(100vw - 40px);

                padding-top: 18vh;
            }}

            .chat-welcome h1 {{

                font-size: 28px;
            }}

            .chat-welcome h3 {{

                font-size: 18px;
            }}

            .suggested-questions {{

                width: calc(100vw - 40px);

                margin-top: 28px;

                margin-bottom: 120px;
            }}

            .suggested-question {{

                font-size: 12px;
            }}

            .ai-message {{

                max-width: 100%;
            }}

            .ai-content {{

                padding-right: 0;

                font-size: 14px;

                line-height: 1.9;
            }}

            .citations-section,
            .evaluation-section {{

                padding-right: 0;
            }}

            .citations-title,
            .citation-item,
            .evaluation-title,
            .evaluation-item,
            .evaluation-item strong {{

                font-size: 13px;
            }}

            .evaluation-items {{

                gap: 10px;
            }}
        }}


        /* =========================================================
           SIDEBAR MOBILE
           ========================================================= */

        @media (max-width: 768px) {{

            section[data-testid="stSidebar"]
            .st-key-sidebar_user_section {{

                padding-left: 12px !important;

                padding-right: 12px !important;
            }}
        }}


        /* =========================================================
           LARGE SCREENS
           ========================================================= */

        @media (min-width: 1200px) {{

            [data-testid="stForm"] {{

                width: 100% !important;
            }}
        }}


        /* =========================================================
           ADMIN / USER MANAGEMENT
           ========================================================= */


        /* =========================================================
           ADMIN PAGE
           ========================================================= */

        .st-key-admin_page {{

            width: 100% !important;

            max-width: 1150px !important;

            margin: 0 auto !important;

            padding: 20px 20px 30px 20px !important;

            box-sizing: border-box !important;

            direction: rtl !important;
        }}


        /* =========================================================
           ADMIN HEADER
           ========================================================= */

        .st-key-admin_page .admin-header-title {{

            color: #FFFFFF !important;

            font-size: 28px !important;

            font-weight: 600 !important;

            line-height: 1.5 !important;

            margin: 0 0 5px 0 !important;

            text-align: right !important;
        }}

        .st-key-admin_page .admin-header-subtitle {{

            color: #8E8E8E !important;

            font-size: 14px !important;

            line-height: 1.8 !important;

            margin: 0 !important;

            text-align: right !important;
        }}


        /* =========================================================
           ADD USER BUTTON
           ========================================================= */

        .st-key-add_user_button button {{

            height: 42px !important;

            min-height: 42px !important;

            padding: 0 17px !important;

            background-color: #3B82F6 !important;

            color: #FFFFFF !important;

            border: none !important;

            border-radius: 10px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;

            font-weight: 500 !important;

            box-shadow: none !important;

            transition:
                background-color 0.15s ease,
                transform 0.15s ease !important;
        }}

        .st-key-add_user_button button:hover {{

            background-color: #2563EB !important;

            transform: translateY(-1px) !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           ADD USER FORM
           ========================================================= */

        .st-key-admin_add_form {{

            width: 100% !important;

            background-color: #2F2F2F !important;

            border: 1px solid #3A3A3A !important;

            border-radius: 14px !important;

            padding: 21px !important;

            margin: 12px 0 24px 0 !important;

            box-sizing: border-box !important;

            direction: rtl !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           EDIT USER FORM
           ========================================================= */

        [class*="st-key-admin_edit_form_"] {{

            width: calc(100% - 0px) !important;

            background-color: #292929 !important;

            border: 1px solid #414141 !important;

            border-radius: 12px !important;

            padding: 20px !important;

            margin: 14px 0 8px 0 !important;

            box-sizing: border-box !important;

            direction: rtl !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           FORM TITLES
           ========================================================= */

        .st-key-admin_add_form .admin-form-title,
        [class*="st-key-admin_edit_form_"] .admin-form-title {{

            color: #FFFFFF !important;

            font-size: 18px !important;

            font-weight: 600 !important;

            line-height: 1.5 !important;

            margin-bottom: 5px !important;

            text-align: right !important;
        }}

        .st-key-admin_add_form .admin-form-subtitle,
        [class*="st-key-admin_edit_form_"] .admin-form-subtitle {{

            color: #8E8E8E !important;

            font-size: 13px !important;

            font-weight: 400 !important;

            line-height: 1.7 !important;

            text-align: right !important;
        }}

        .admin-edit-username {{

            color: #777777 !important;

            font-size: 13px !important;

            direction: ltr !important;

            text-align: right !important;

            margin-top: 2px !important;
        }}


        /* =========================================================
           ADMIN FORM LABELS
           ========================================================= */

        .st-key-admin_add_form
        [data-testid="stTextInput"] label,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stTextInput"] label,

        .st-key-admin_add_form
        [data-testid="stSelectbox"] label,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stSelectbox"] label {{

            color: #D4D4D4 !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;

            font-weight: 500 !important;

            direction: rtl !important;

            text-align: right !important;
        }}


        /* =========================================================
           ADMIN INPUTS
           ========================================================= */

        .st-key-admin_add_form
        [data-testid="stTextInput"] input,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stTextInput"] input {{

            width: 100% !important;

            height: 44px !important;

            min-height: 44px !important;

            background-color: #242424 !important;

            color: #FFFFFF !important;

            border: 1px solid #454545 !important;

            border-radius: 9px !important;

            padding: 0 13px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;

            direction: rtl !important;

            text-align: right !important;

            box-shadow: none !important;

            outline: none !important;
        }}

        .st-key-admin_add_form
        [data-testid="stTextInput"] input::placeholder,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stTextInput"] input::placeholder {{

            color: #707070 !important;

            font-size: 13px !important;
        }}

        .st-key-admin_add_form
        [data-testid="stTextInput"] input:focus,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stTextInput"] input:focus {{

            border-color: #3B82F6 !important;

            box-shadow:
                0 0 0 1px rgba(59, 130, 246, 0.45) !important;
        }}


        /* =========================================================
           ADMIN SELECTBOX
           ========================================================= */

        .st-key-admin_add_form
        [data-testid="stSelectbox"]
        [data-baseweb="select"] > div,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stSelectbox"]
        [data-baseweb="select"] > div {{

            min-height: 44px !important;

            background-color: #242424 !important;

            border: 1px solid #454545 !important;

            border-radius: 9px !important;

            color: #FFFFFF !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;
        }}

        .st-key-admin_add_form
        [data-testid="stSelectbox"] span,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stSelectbox"] span {{

            color: #FFFFFF !important;

            font-size: 14px !important;
        }}


        /* =========================================================
           ADMIN FORM BUTTONS
           ========================================================= */

        .st-key-admin_add_form
        [data-testid="stFormSubmitButton"] button,

        [class*="st-key-admin_edit_form_"]
        [data-testid="stFormSubmitButton"] button {{

            height: 42px !important;

            min-height: 42px !important;

            border-radius: 9px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 13px !important;

            font-weight: 500 !important;

            box-shadow: none !important;
        }}


        /* =========================================================
           STATISTICS
           ========================================================= */

        .st-key-admin_stats {{

            width: 100% !important;

            margin: 10px 0 30px 0 !important;

            direction: rtl !important;
        }}

        .st-key-admin_stats [data-testid="column"] {{

            padding-left: 5px !important;

            padding-right: 5px !important;
        }}

        .admin-stat-card {{

            width: 100% !important;

            min-height: 105px !important;

            background-color: #2F2F2F !important;

            border: 1px solid #3A3A3A !important;

            border-radius: 12px !important;

            padding: 18px 19px !important;

            box-sizing: border-box !important;

            direction: rtl !important;

            text-align: right !important;

            transition:
                background-color 0.15s ease,
                border-color 0.15s ease !important;
        }}

        .admin-stat-card:hover {{

            background-color: #323232 !important;

            border-color: #454545 !important;
        }}

        .admin-stat-label {{

            color: #8E8E8E !important;

            font-size: 13px !important;

            font-weight: 400 !important;

            margin-bottom: 7px !important;
        }}

        .admin-stat-value {{

            color: #FFFFFF !important;

            font-size: 27px !important;

            font-weight: 600 !important;

            line-height: 1.2 !important;
        }}


        /* =========================================================
           USER SECTION
           ========================================================= */

        .st-key-admin_user_section {{

            width: 100% !important;

            direction: rtl !important;

            text-align: right !important;

            margin-bottom: 10px !important;
        }}

        .st-key-admin_user_section .admin-section-title {{

            color: #FFFFFF !important;

            font-size: 20px !important;

            font-weight: 600 !important;

            line-height: 1.5 !important;

            margin-bottom: 3px !important;

            text-align: right !important;
        }}

        .st-key-admin_user_section .admin-section-subtitle {{

            color: #8E8E8E !important;

            font-size: 13px !important;

            line-height: 1.7 !important;

            text-align: right !important;
        }}


        /* =========================================================
           SEARCH
           ========================================================= */

        .st-key-admin_user_section
        [data-testid="stTextInput"] input {{

            height: 44px !important;

            min-height: 44px !important;

            background-color: #2F2F2F !important;

            color: #FFFFFF !important;

            border: 1px solid #414141 !important;

            border-radius: 10px !important;

            padding: 0 13px !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 14px !important;

            direction: rtl !important;

            text-align: right !important;

            box-shadow: none !important;
        }}

        .st-key-admin_user_section
        [data-testid="stTextInput"] input::placeholder {{

            color: #707070 !important;

            font-size: 13px !important;
        }}

        .st-key-admin_user_section
        [data-testid="stTextInput"] input:focus {{

            border-color: #3B82F6 !important;

            box-shadow:
                0 0 0 1px rgba(59, 130, 246, 0.4) !important;
        }}


        /* =========================================================
           USER LIST
           ========================================================= */

        .st-key-admin_users_list {{

            width: 100% !important;

            direction: rtl !important;

            margin-top: 8px !important;
        }}


        /* =========================================================
           USER CARD
           ========================================================= */

        .st-key-admin_users_list
        [class*="st-key-admin_user_"] {{

            width: 100% !important;

            background-color: #2F2F2F !important;

            border: 1px solid #3A3A3A !important;

            border-radius: 12px !important;

            padding: 15px 17px !important;

            margin-bottom: 9px !important;

            box-sizing: border-box !important;

            direction: rtl !important;

            transition:
                background-color 0.15s ease,
                border-color 0.15s ease !important;
        }}

        .st-key-admin_users_list
        [class*="st-key-admin_user_"]:hover {{

            background-color: #323232 !important;

            border-color: #454545 !important;
        }}


       
        



/* =========================================================
   USER INFO
   ========================================================= */

.admin-user-info {{
    width: 100% !important;

    min-height: 48px !important;

    display: flex !important;

    flex-direction: column !important;

    justify-content: center !important;

    box-sizing: border-box !important;

    direction: rtl !important;

    text-align: right !important;

    overflow: hidden !important;
}}


.admin-user-label {{
    color: #777777 !important;

    font-size: 12px !important;

    font-weight: 400 !important;

    line-height: 1.5 !important;

    margin-bottom: 4px !important;

    white-space: nowrap !important;

    text-align: right !important;
}}


.admin-user-name {{
    color: #FFFFFF !important;

    font-size: 17px !important;

    font-weight: 600 !important;

    line-height: 1.6 !important;

    white-space: nowrap !important;

    overflow: hidden !important;

    text-overflow: ellipsis !important;

    text-align: right !important;
}}


.admin-user-username {{
    color: #B0B0B0 !important;

    font-size: 14px !important;

    line-height: 1.6 !important;

    direction: ltr !important;

    text-align: right !important;

    white-space: nowrap !important;

    overflow: hidden !important;

    text-overflow: ellipsis !important;
}}


.admin-user-detail {{
    color: #D4D4D4 !important;

    font-size: 14px !important;

    line-height: 1.6 !important;

    white-space: nowrap !important;

    overflow: hidden !important;

    text-overflow: ellipsis !important;

    text-align: right !important;
}}


.admin-user-level {{
    color: #BDBDBD !important;

    font-size: 14px !important;

    line-height: 1.6 !important;

    white-space: nowrap !important;

    text-align: right !important;
}}




        /* =========================================================
           STATUS
           ========================================================= */

        .admin-status {{

            display: inline-flex !important;

            align-items: center !important;

            justify-content: center !important;

            min-width: 60px !important;

            height: 29px !important;

            padding: 0 10px !important;

            border-radius: 7px !important;

            font-size: 12px !important;

            font-weight: 500 !important;

            box-sizing: border-box !important;

            white-space: nowrap !important;
        }}

        .admin-status-active {{

            background-color: rgba(34, 197, 94, 0.10) !important;

            color: #86EFAC !important;

            border:
                1px solid rgba(34, 197, 94, 0.20) !important;
        }}

        .admin-status-inactive {{

            background-color: rgba(239, 68, 68, 0.10) !important;

            color: #FCA5A5 !important;

            border:
                1px solid rgba(239, 68, 68, 0.18) !important;
        }}


        /* =========================================================
           USER ACTION BUTTONS
           ========================================================= */

       .st-key-admin_users_list
[class*="st-key-admin_user_"] {{
    width: 100% !important;

    background-color: #2F2F2F !important;

    border: 1px solid #3A3A3A !important;

    border-radius: 12px !important;

    padding: 16px 18px !important;

    margin-bottom: 10px !important;

    box-sizing: border-box !important;

    direction: rtl !important;

    overflow: visible !important;

    transition:
        background-color 0.15s ease,
        border-color 0.15s ease !important;
}}

        .st-key-admin_users_list
        [class*="st-key-admin_user_"]
        .stButton > button:hover {{

            transform: none !important;
        }}


        /* =========================================================
           EMPTY STATE
           ========================================================= */

        .admin-empty-state {{

            width: 100% !important;

            background-color: #2F2F2F !important;

            border: 1px solid #3A3A3A !important;

            border-radius: 12px !important;

            padding: 36px 20px !important;

            margin-top: 8px !important;

            box-sizing: border-box !important;

            text-align: center !important;
        }}

        .admin-empty-title {{

            color: #D0D0D0 !important;

            font-size: 15px !important;

            font-weight: 500 !important;
        }}

        .admin-empty-subtitle {{

            color: #777777 !important;

            font-size: 13px !important;

            margin-top: 5px !important;
        }}


        /* =========================================================
           ADMIN ALERTS
           ========================================================= */

        .st-key-admin_page
        [data-testid="stAlert"],

        .st-key-admin_add_form
        [data-testid="stAlert"],

        [class*="st-key-admin_edit_form_"]
        [data-testid="stAlert"] {{

            border-radius: 10px !important;

            direction: rtl !important;

            text-align: right !important;

            font-family: 'Vazirmatn', sans-serif !important;

            font-size: 13px !important;
        }}


        /* =========================================================
           ADMIN DIVIDERS
           ========================================================= */

        .st-key-admin_page hr {{

            border-color: #3A3A3A !important;
        }}


        /* =========================================================
           ADMIN RESPONSIVE
           ========================================================= */

        @media (max-width: 1100px) {{

            .admin-user-row {{

                gap: 18px !important;
            }}

            .admin-user-main {{

                min-width: 105px !important;
            }}

            .admin-user-detail {{

                max-width: 150px !important;
            }}
        }}


        @media (max-width: 900px) {{

            .st-key-admin_page {{

                padding: 16px 12px 50px 12px !important;
            }}

            .st-key-admin_page .admin-header-title {{

                font-size: 25px !important;
            }}

            .st-key-admin_stats [data-testid="column"] {{

                padding-left: 3px !important;

                padding-right: 3px !important;
            }}

            .admin-user-row {{

                gap: 14px !important;

                flex-wrap: wrap !important;
            }}

            .admin-user-block {{

                min-width: 110px !important;
            }}

            .admin-user-main {{

                min-width: 130px !important;
            }}
        }}


        @media (max-width: 700px) {{

            .st-key-admin_page {{

                padding: 12px 10px 45px 10px !important;
            }}

            .st-key-admin_page .admin-header-title {{

                font-size: 22px !important;
            }}

            .st-key-admin_page .admin-header-subtitle {{

                font-size: 12px !important;
            }}

            .st-key-admin_stats [data-testid="column"] {{

                width: 100% !important;

                flex: 1 1 100% !important;
            }}

            .st-key-admin_stats [data-testid="column"]
            + [data-testid="column"] {{

                margin-top: 8px !important;
            }}

            .st-key-admin_users_list
            [class*="st-key-admin_user_"] {{

                padding: 14px !important;
            }}

            .admin-user-row {{

                display: grid !important;

                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;

                gap: 14px !important;
            }}

            .admin-user-block,

            .admin-user-main {{

                min-width: 0 !important;

                max-width: none !important;
            }}

            .admin-user-name {{

                font-size: 15px !important;
            }}

            .admin-user-detail,

            .admin-user-level,

            .admin-user-username {{

                font-size: 13px !important;
            }}

            [class*="st-key-admin_edit_form_"] {{

                padding: 16px !important;
            }}
        }}


        </style>
        """,
        unsafe_allow_html=True
    )

