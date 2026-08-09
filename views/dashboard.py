import streamlit as st

from config import ACCENT, APP_NAME
from utils import api_client
from utils.formatting import format_when
from utils.me import get_leaves_taken, get_goals_due, manager_badge_html
from utils.state import current_user, log_out


def _kpi_card(label: str, value: str, value_size: str = "1.2rem", sub_note: str | None = None):
    sub_html = (
        f'<div style="font-size:0.68rem;color:#DC2626;font-weight:600;margin-top:0.15rem;">{sub_note}</div>'
        if sub_note
        else ""
    )
    html = (
        '<div style="background:white;border-radius:14px;padding:0.9rem 1.1rem;'
        'border:1px solid #ECEEF5;box-shadow:0 1px 2px rgba(16,24,40,0.04);min-height:92px;">'
        f'<div style="font-size:{value_size};font-weight:700;color:#1E2233;'
        f'line-height:1.3;word-break:break-word;">{value}</div>'
        f'<div style="color:#6B7280;font-size:0.75rem;margin-top:0.25rem;">{label}</div>'
        f'{sub_html}'
        f'<div style="height:3px;width:24px;background:{ACCENT};border-radius:2px;margin-top:0.5rem;"></div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _thread_title(t: dict, max_len: int = 60) -> str:
    title = (t.get("THREAD_TITLE") or "New chat").strip()
    title = " ".join(title.split())
    return title[:max_len].rstrip() + "…" if len(title) > max_len else title


def _activity_row(t: dict):
    st.markdown(
        f"""
        <div style="display:flex; align-items:flex-start; gap:0.65rem;
                    padding:0.6rem 0; border-bottom:1px solid #F1F2F8;">
            <div style="width:7px; height:7px; border-radius:50%; background:{ACCENT};
                        margin-top:0.4rem; flex-shrink:0;"></div>
            <div>
                <div style="font-size:0.85rem; color:#1E2233;">{_thread_title(t)}</div>
                <div style="font-size:0.72rem; color:#9CA3AF;">{format_when(t.get('UPDATED_AT'))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_days(value) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "0"
    return f"{f:g}"


def render():
    user = current_user()

    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.55rem;">
                <div style="width:34px; height:34px; border-radius:9px;
                            background:linear-gradient(135deg,{ACCENT},#7C3AED);
                            color:white; display:flex; align-items:center; justify-content:center;
                            font-weight:700; font-size:0.85rem;">IQ</div>
                <div>
                    <div style="font-weight:700; font-size:1.05rem;">{APP_NAME} — Dashboard</div>
                    <div style="color:#6B7280; font-size:0.78rem;">Connected to your live data</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_r:
        st.markdown(
            f'<div style="text-align:right;">'
            f'<div style="color:#1E2233;font-weight:600;font-size:0.85rem;">{user["email"]}</div>'
            f'{manager_badge_html(user, ACCENT)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.write("")

    try:
        threads = api_client.list_threads(user["token"])
    except api_client.ApiError as e:
        if e.status_code == 401:
            log_out("Your session expired — please log in again.")
            st.rerun()
        st.error(f"Couldn't load your conversations: {e}")
        threads = []

    threads_sorted = sorted(threads, key=lambda t: t.get("UPDATED_AT") or 0, reverse=True)

    leaves = get_leaves_taken(user)
    goals = get_goals_due(user)
    overdue = goals.get("overdue_goals") or 0

    cols = st.columns(4)
    with cols[0]:
        _kpi_card("Conversations", str(len(threads)))
    with cols[1]:
        _kpi_card("Leave days taken (YTD)", _format_days(leaves.get("total_days_this_year")))
    with cols[2]:
        _kpi_card(
            "Goals due",
            str(goals.get("open_goals_due", 0)),
            sub_note=f"{overdue} overdue" if overdue else None,
        )
    with cols[3]:
        _kpi_card(
            "Last active",
            format_when(threads_sorted[0].get("UPDATED_AT")) if threads_sorted else "—",
            value_size="1rem",
        )

    st.write("")
    left, right = st.columns([2, 1])

    with left:
        st.markdown("###### Recent activity")
        with st.container(border=True):
            if not threads_sorted:
                st.markdown(
                    "<p style='color:#9CA3AF; text-align:center; margin:2rem 0; font-size:0.85rem;'>"
                    "No conversations yet — start one from the chat page.</p>",
                    unsafe_allow_html=True,
                )
            for t in threads_sorted[:6]:
                _activity_row(t)

    with right:
        st.markdown("###### Ask the HR agent")
        with st.container(border=True):
            st.markdown(
                "<p style='font-size:0.85rem; color:#374151;'>Have a question about pay, "
                "leave, goals, or policy?</p>",
                unsafe_allow_html=True,
            )
            if st.button("Open chat →", use_container_width=True, type="primary"):
                st.switch_page("views/chat.py")


render()