"""
Thin caching layer over the /me/* endpoints. Each is fetched at most once
per session (cleared on logout by utils.state.log_out) since this data
doesn't change mid-session.
"""
import streamlit as st

from utils import api_client
from utils.state import log_out


def _cached(key: str, fetch_fn, user: dict) -> dict:
    if key not in st.session_state:
        try:
            st.session_state[key] = fetch_fn(user["token"])
        except api_client.ApiError as e:
            if e.status_code == 401:
                log_out("Your session expired — please log in again.")
                st.rerun()
            st.session_state[key] = {}
    return st.session_state[key]


def get_manager(user: dict) -> dict:
    return _cached("_me_manager", api_client.get_my_manager, user)


def get_leaves_taken(user: dict) -> dict:
    return _cached("_me_leaves", api_client.get_my_leaves_taken, user)


def get_goals_due(user: dict) -> dict:
    return _cached("_me_goals", api_client.get_my_goals_due, user)


def manager_badge_html(user: dict, accent: str = "#4F46E5") -> str:
    """A small 'Reports to <name>' line -- empty string (renders nothing)
    if the caller has no manager. Plain text rather than a pill/chip shape
    on purpose: a chip that wraps onto two lines in a narrow sidebar looks
    broken, whereas text wrapping is normal."""
    name = get_manager(user).get("manager_name")
    if not name:
        return ""
    return (
        f'<div style="font-size:0.72rem;color:{accent};font-weight:600;'
        f'margin-top:0.3rem;line-height:1.3;">Reports to {name}</div>'
    )