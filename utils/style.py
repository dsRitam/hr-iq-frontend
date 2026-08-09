import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        [data-testid="stChatMessageContent"] p { font-size: 0.87rem; line-height: 1.55; }
        [data-testid="stChatMessageContent"] li { font-size: 0.87rem; }
        [data-testid="stChatMessageContent"] { padding-top: 0.4rem; padding-bottom: 0.4rem; }
        [data-testid="stChatInput"] textarea { font-size: 0.82rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )