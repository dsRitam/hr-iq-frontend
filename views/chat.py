import streamlit as st

from config import APP_NAME
from utils import api_client
from utils.formatting import format_when
from utils.state import current_user, log_out


def _thread_title(t: dict, max_len: int = 30) -> str:
    title = (t.get("THREAD_TITLE") or "New chat").strip()
    title = " ".join(title.split())
    return title[:max_len].rstrip() + "…" if len(title) > max_len else title


def _to_number(value):
    """Snowflake's SQL API returns NUMBER columns as JSON strings, not
    native numbers -- TIME_TAKEN_MS comes back as e.g. "1840", not 1840.
    Dividing a string caused the TypeError; coerce it here once instead
    of at every use site."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flatten_api_messages(raw_rows: list) -> list:
    """The backend stores one row per question+answer pair. Split each
    into a user bubble + an assistant bubble."""
    flat = []
    for row in raw_rows:
        flat.append({"role": "user", "text": row.get("QUESTION", "")})
        flat.append(
            {
                "role": "assistant",
                "text": row.get("ANSWER", ""),
                "sql_queries": row.get("SQL_QUERIES_JSON") or [],
                "rows": row.get("ROWS_JSON") or [],
                "time_taken_ms": _to_number(row.get("TIME_TAKEN_MS")),
            }
        )
    return flat


def _messages_key(thread_id) -> str:
    return "_messages_new" if thread_id is None else f"_messages_{thread_id}"


def _load_messages(user: dict, thread_id) -> list:
    key = _messages_key(thread_id)
    if key not in st.session_state:
        if thread_id is None:
            st.session_state[key] = []
        else:
            try:
                raw = api_client.list_messages(user["token"], thread_id)
            except api_client.ApiError as e:
                if e.status_code == 401:
                    log_out("Your session expired — please log in again.")
                    st.rerun()
                st.error(f"Couldn't load this conversation: {e}")
                raw = []
            st.session_state[key] = _flatten_api_messages(raw)
    return st.session_state[key]


def _all_threads(user: dict) -> list:
    if "_threads_cache" not in st.session_state:
        try:
            st.session_state["_threads_cache"] = api_client.list_threads(user["token"])
        except api_client.ApiError as e:
            if e.status_code == 401:
                log_out("Your session expired — please log in again.")
                st.rerun()
            st.error(f"Couldn't load your conversations: {e}")
            st.session_state["_threads_cache"] = []
    return sorted(
        st.session_state["_threads_cache"], key=lambda t: t.get("UPDATED_AT") or 0, reverse=True
    )


def _matches_search(t: dict, query: str) -> bool:
    title = (t.get("THREAD_TITLE") or "").lower()
    return query in title


def _delete_thread(user: dict, thread_id: str):
    try:
        api_client.delete_thread(user["token"], thread_id)
    except api_client.ApiError as e:
        if e.status_code == 401:
            log_out("Your session expired — please log in again.")
            st.rerun()
        st.toast(f"Couldn't delete that conversation: {e}")
        return
    st.session_state.pop(_messages_key(thread_id), None)
    st.session_state.pop("_threads_cache", None)
    if st.session_state.get("active_thread_id") == thread_id:
        st.session_state["active_thread_id"] = None
    st.toast("Conversation deleted.")


def _render_message(m: dict):
    role = "user" if m["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.write(m["text"])

        if role != "assistant":
            return

        time_col, query_col, rows_col, spacer = st.columns([1.3, 0.5, 0.5, 2.2])

        with time_col:
            t_ms = _to_number(m.get("time_taken_ms"))
            if t_ms is not None:
                st.caption(f"⏱ {t_ms / 1000:.1f}s")

        with query_col:
            if m.get("sql_queries"):
                with st.popover("🧾", help="View query executed"):
                    st.markdown("**Query executed**")
                    for q in m["sql_queries"]:
                        st.code(q, language="sql")

        with rows_col:
            if m.get("rows"):
                with st.popover("📊", help="View rows returned"):
                    st.markdown(f"**Rows returned** ({len(m['rows'])})")
                    st.dataframe(m["rows"], use_container_width=True, hide_index=True)


def _inject_history_css():
    st.markdown(
        '<style>'
        'div.history-scope-marker ~ div [data-testid="stButton"] button {'
        'font-size:0.68rem !important;padding:0.25rem 0.4rem !important;'
        'height:2rem !important;min-height:2rem !important;'
        'white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;'
        'display:flex !important;align-items:center !important;justify-content:flex-start !important;'
        '}'
        'div.history-scope-marker ~ div [data-testid="stTextInput"] input {'
        'font-size:0.7rem !important;padding:0.3rem 0.5rem !important;height:2rem !important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )


def render():
    user = current_user()

    st.markdown(
        f'<div style="margin-bottom:0.4rem;">'
        f'<div style="font-weight:700;font-size:0.98rem;">Ask the {APP_NAME} agent</div>'
        f'<div style="color:#6B7280;font-size:0.75rem;">'
        f'Agentic assistant for workforce health, hiring readiness, and people insights</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    history_col, chat_col, action_col = st.columns([1.4, 3.1, 0.22])

    with history_col:
        _inject_history_css()
        st.markdown('<div class="history-scope-marker"></div>', unsafe_allow_html=True)

        if st.button("+ New chat", use_container_width=True):
            st.session_state["active_thread_id"] = None
            st.rerun()
        search_query = st.text_input(
            "Search history", label_visibility="collapsed", placeholder="Search history"
        ).strip().lower()

        threads = _all_threads(user)
        if search_query:
            threads = [t for t in threads if _matches_search(t, search_query)]
        history_pane = st.container(height=250, border=False)
        with history_pane:
            for t in threads:
                tid = t["THREAD_ID"]
                active = st.session_state.get("active_thread_id") == tid

                col_main, col_del = st.columns([4, 1])
                with col_main:
                    if st.button(
                        _thread_title(t),
                        key=f"thread_{tid}",
                        use_container_width=True,
                        type="primary" if active else "secondary",
                    ):
                        st.session_state["active_thread_id"] = tid
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{tid}", help="Delete this conversation"):
                        _delete_thread(user, tid)
                        st.rerun()
                st.markdown(
                    f'<div style="font-size:0.6rem;color:#9CA3AF;margin:-0.3rem 0 0.3rem 0.15rem;">'
                    f'{format_when(t.get("UPDATED_AT"))}</div>',
                    unsafe_allow_html=True,
                )
            if not threads:
                empty_msg = "No conversations match your search." if search_query else "No conversations yet."
                st.markdown(
                    f"<p style='color:#9CA3AF; font-size:0.75rem; text-align:center; margin-top:1rem;'>"
                    f"{empty_msg}</p>",
                    unsafe_allow_html=True,
                )

    with chat_col:
        thread_id = st.session_state.get("active_thread_id")
        messages = _load_messages(user, thread_id)

        chat_box = st.container(height=360, border=True)
        with chat_box:
            if not messages:
                st.markdown(
                    "<p style='color:#9CA3AF; text-align:center; margin-top:3rem; font-size:0.85rem;'>"
                    "Start a new conversation below.</p>",
                    unsafe_allow_html=True,
                )
            for m in messages:
                _render_message(m)

        prompt = st.chat_input("Ask the agent anything — \"who on my team is likely to have unapplied leave?\"")
        if prompt:
            messages.append({"role": "user", "text": prompt})

            done_payload = None
            error_detail = None
            error_status = None
            full_reply = ""

            with chat_box:
                with st.chat_message("user"):
                    st.write(prompt)
                with st.chat_message("assistant"):
                    status_ph = st.empty()
                    reply_ph = st.empty()
                    status_ph.caption("⏳ Thinking…")

                    for evt in api_client.stream_ask(user["token"], prompt, thread_id):
                        etype, data = evt["type"], evt["data"]
                        if etype == "step":
                            status_ph.caption(f"⏳ {data.get('text', '')}")
                        elif etype == "answer_delta":
                            status_ph.empty()
                            full_reply += data.get("text", "")
                            reply_ph.write(full_reply)
                        elif etype == "done":
                            status_ph.empty()
                            done_payload = data
                        elif etype == "error":
                            status_ph.empty()
                            error_detail = data.get("detail", "Something went wrong.")
                            error_status = data.get("status_code")

                    if error_detail:
                        reply_ph.error(error_detail)

            if error_status == 401:
                log_out("Your session expired — please log in again.")
                st.rerun()

            if done_payload:
                new_thread_id = done_payload.get("thread_id")
                if thread_id is None and new_thread_id:
                    st.session_state[_messages_key(new_thread_id)] = st.session_state.pop(_messages_key(None))
                    st.session_state["active_thread_id"] = new_thread_id
                target_key = _messages_key(new_thread_id or thread_id)
                st.session_state[target_key].append(
                    {
                        "role": "assistant",
                        "text": done_payload.get("answer", full_reply),
                        "sql_queries": done_payload.get("sql_queries") or [],
                        "rows": done_payload.get("rows") or [],
                        "time_taken_ms": _to_number(done_payload.get("time_taken_ms")),
                    }
                )
                st.session_state.pop("_threads_cache", None)
            elif not error_detail:
                messages.append(
                    {"role": "assistant", "text": "No response received from the assistant."}
                )

            st.rerun()

    with action_col:
        st.write("")
        if st.button("👥", key="teams_action", use_container_width=True, help="Send to Teams"):
            st.toast("Sending to Teams isn't wired up on the backend yet.")
        if st.button("✉️", key="email_action", use_container_width=True, help="Send by email"):
            st.toast("Emailing this conversation isn't wired up on the backend yet.")

    st.markdown(
        "<p style='color:#B0B4C3; font-size:0.68rem; margin-top:0.4rem;'>"
        "Connected to the live HR IQ agent — answers, query/rows, and "
        "timing are real."
        "</p>",
        unsafe_allow_html=True,
    )


render()