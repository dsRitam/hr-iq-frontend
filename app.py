import streamlit as st

from config import ACCENT, APP_NAME
from utils.state import (
    init_state, is_authenticated, current_user, log_out, log_in,
    current_app, exit_to_landing,
)
from utils.style import inject_global_css
from utils.me import manager_badge_html

st.set_page_config(page_title=APP_NAME, page_icon="🟣", layout="wide")
init_state()
inject_global_css()


def _handle_sso_redirect():
    """Catches the query params /auth/sso/callback (backend) redirects
    the browser to, and logs the person in automatically. A no-op on
    every normal page load -- st.query_params is empty then."""
    params = st.query_params

    if "sso_error" in params:
        st.session_state["_sso_error_message"] = params["sso_error"]
        st.query_params.clear()
        st.rerun()

    if "token" in params and not is_authenticated():
        log_in({
            "email": params.get("email", ""),
            "token": params["token"],
            "hr_features_access": params.get("hr_features_access", "false").lower() == "true",
        })
        st.query_params.clear()
        st.rerun()


_handle_sso_redirect()

if not is_authenticated():
    pg = st.navigation([st.Page("views/auth.py", title="Log in", icon="🔐")])
else:
    user = current_user()
    app_id = current_app()
    in_hr_iq = app_id == "hr_iq"

    with st.sidebar:
        st.markdown(
            f'<div style="padding:0.5rem 0 1rem 0;">'
            f'<div style="font-weight:700;font-size:0.88rem;word-break:break-all;">{user["email"]}</div>'
            f'{manager_badge_html(user, ACCENT) if in_hr_iq else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if app_id is not None:
            if st.button("← Back to Workspace", use_container_width=True):
                exit_to_landing()
                st.rerun()
        if st.button("Log out", use_container_width=True):
            log_out()
            st.rerun()

    if in_hr_iq:
        pg = st.navigation(
            [
                st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
                st.Page("views/chat.py", title="Ask HR Agent", icon="💬"),
            ]
        )
    else:
        pg = st.navigation([st.Page("views/landing.py", title="Workspace", icon="🗂️")])

pg.run()