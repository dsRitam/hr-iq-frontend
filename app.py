import streamlit as st

from config import ACCENT, APP_NAME
from utils.state import init_state, is_authenticated, current_user, log_out
from utils.style import inject_global_css
from utils.me import manager_badge_html

st.set_page_config(page_title=APP_NAME, page_icon="🟣", layout="wide")
init_state()
inject_global_css()

if not is_authenticated():
    pg = st.navigation([st.Page("views/auth.py", title="Log in", icon="🔐")])
else:
    user = current_user()

    with st.sidebar:
        st.markdown(
            f'<div style="padding:0.5rem 0 1rem 0;">'
            f'<div style="font-weight:700;font-size:0.88rem;word-break:break-all;">{user["email"]}</div>'
            f'{manager_badge_html(user, ACCENT)}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True):
            log_out()
            st.rerun()

    pg = st.navigation(
        [
            st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
            st.Page("views/chat.py", title="Ask HR Agent", icon="💬"),
        ]
    )

pg.run()