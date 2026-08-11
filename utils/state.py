import streamlit as st


def init_state():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("active_thread_id", None)
    st.session_state.setdefault("current_app", None)  # None = workspace landing page


def is_authenticated() -> bool:
    return st.session_state.get("user") is not None


def current_user() -> dict | None:
    return st.session_state.get("user")


def log_in(user: dict):
    """user = {"email": ..., "token": ..., "hr_features_access": ...}.
    hr_features_access comes directly from the SSO callback's redirect
    for that path; local email/password login's /auth/login response
    doesn't include it, so the caller must fetch it separately right
    after (see api_client.get_my_hr_features_access) and include it here."""
    st.session_state["user"] = user
    st.session_state["active_thread_id"] = None
    st.session_state["current_app"] = None


_ME_CACHE_KEYS = {"_me_manager", "_me_leaves", "_me_goals"}


def log_out(message: str | None = None):
    st.session_state["user"] = None
    st.session_state["active_thread_id"] = None
    st.session_state["current_app"] = None
    # Clear any cached per-thread messages / thread list / /me data so
    # nothing from the previous session leaks into the next login.
    for key in [
        k for k in st.session_state.keys()
        if k.startswith("_messages_") or k == "_threads_cache" or k in _ME_CACHE_KEYS
    ]:
        del st.session_state[key]
    if message:
        st.session_state["_logout_message"] = message


def current_app() -> str | None:
    """None = the workspace landing page. Otherwise the id of whichever
    app the person clicked "Enter workspace" on (e.g. "hr_iq")."""
    return st.session_state.get("current_app")


def enter_app(app_id: str):
    st.session_state["current_app"] = app_id
    st.session_state["active_thread_id"] = None


def exit_to_landing():
    st.session_state["current_app"] = None