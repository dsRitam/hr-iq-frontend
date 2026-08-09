import streamlit as st


def init_state():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("active_thread_id", None)


def is_authenticated() -> bool:
    return st.session_state.get("user") is not None


def current_user() -> dict | None:
    return st.session_state.get("user")


def log_in(user: dict):
    """user = {"email": ..., "token": ...} from api_client.login()."""
    st.session_state["user"] = user
    st.session_state["active_thread_id"] = None


_ME_CACHE_KEYS = {"_me_manager", "_me_leaves", "_me_goals"}


def log_out(message: str | None = None):
    st.session_state["user"] = None
    st.session_state["active_thread_id"] = None
    # Clear any cached per-thread messages / thread list / /me data so
    # nothing from the previous session leaks into the next login.
    for key in [
        k for k in st.session_state.keys()
        if k.startswith("_messages_") or k == "_threads_cache" or k in _ME_CACHE_KEYS
    ]:
        del st.session_state[key]
    if message:
        st.session_state["_logout_message"] = message