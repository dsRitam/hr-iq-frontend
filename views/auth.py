import streamlit as st

from config import APP_NAME, APP_TAGLINE
from utils import api_client
from utils.state import log_in


def _header():
    st.markdown(
        f"""
        <div style="text-align:center; padding-top: 2.5rem; padding-bottom: 0.5rem;">
            <div style="
                display:inline-flex; align-items:center; justify-content:center;
                width:56px; height:56px; border-radius:14px;
                background:linear-gradient(135deg,#4F46E5,#7C3AED);
                color:white; font-weight:700; font-size:1.3rem; margin-bottom:0.75rem;">
                IQ
            </div>
            <h2 style="margin:0; font-weight:700;">{APP_NAME}</h2>
            <p style="color:#6B7280; margin-top:0.15rem;">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _login_form():
    with st.form("login_form", border=False):
        email = st.text_input("Work email", placeholder="you@kpipartners.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Enter your email and password.")
            return
        try:
            user = api_client.login(email, password)
            log_in(user)
            st.rerun()
        except api_client.ApiError as e:
            st.error(str(e))


def _register_form():
    st.caption(
        "Registration sets a password for your existing work email — it "
        "doesn't create a new employee record, so the email must already "
        "be recognized by HR IQ."
    )
    with st.form("register_form", border=False):
        email = st.text_input("Work email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Enter your email and password.")
            return
        if password != confirm:
            st.error("Passwords don't match.")
            return
        try:
            api_client.register(email, password)
            st.success("Account created — you can log in now.")
        except api_client.ApiError as e:
            st.error(str(e))


def render():
    _header()

    logout_msg = st.session_state.pop("_logout_message", None)
    if logout_msg:
        st.warning(logout_msg)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.container(height=10, border=False)
        tab_login, tab_register = st.tabs(["Log in", "Register"])
        with tab_login:
            _login_form()
        with tab_register:
            _register_form()

    st.markdown(
        "<p style='text-align:center; color:#9CA3AF; margin-top:2rem; font-size:0.8rem;'>"
        "Connected to the HR IQ backend."
        "</p>",
        unsafe_allow_html=True,
    )


render()