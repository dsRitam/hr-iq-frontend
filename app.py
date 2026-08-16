"""
Internal testing UI for HR IQ. Not the real frontend -- a separate UI
team owns that. This just lets us exercise the API directly: pick an
email + platform, chat, browse/delete threads and messages.

Auth right now is a placeholder on the backend (bearer token = email,
no real verification) -- so that's all this sends too.
"""
import requests
import streamlit as st

st.set_page_config(page_title="HR IQ (internal test)", layout="wide")

API_BASE_URL = st.secrets.get("API_BASE_URL")
if not API_BASE_URL:
    st.error("API_BASE_URL isn't configured. Set it in .streamlit/secrets.toml (local) "
              "or Streamlit Cloud's app Settings → Secrets (deployed).")
    st.stop()


# ---------------------------------------------------------------- api calls

def _headers():
    return {"Authorization": f"Bearer {st.session_state.email}"}


def api_ask(question, thread_id):
    body = {"question": question, "platform": st.session_state.platform}
    if thread_id:
        body["thread_id"] = thread_id
    resp = requests.post(f"{API_BASE_URL}/ask", json=body, headers=_headers(), timeout=120)
    resp.raise_for_status()
    return resp.json()


def api_get_threads():
    resp = requests.get(f"{API_BASE_URL}/threads", params={"platform": st.session_state.platform},
                         headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["threads"]


def api_get_messages(thread_id):
    resp = requests.get(f"{API_BASE_URL}/threads/{thread_id}/messages",
                         params={"platform": st.session_state.platform}, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["messages"]


def api_delete_thread(thread_id):
    requests.delete(f"{API_BASE_URL}/threads/{thread_id}", params={"platform": st.session_state.platform},
                     headers=_headers(), timeout=30)


def api_delete_message(message_id):
    requests.delete(f"{API_BASE_URL}/messages/{message_id}", params={"platform": st.session_state.platform},
                     headers=_headers(), timeout=30)


# ------------------------------------------------------------- login screen

def render_login():
    st.markdown("<h2 style='text-align:center;'>HR IQ — internal test UI</h2>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.form("login"):
            email = st.text_input("Work email", placeholder="you@kpipartners.com")
            platform = st.selectbox("Platform", ["snowflake", "databricks"])
            submitted = st.form_submit_button("Enter", use_container_width=True, type="primary")
        if submitted:
            if not email.strip():
                st.error("Enter an email.")
                return
            st.session_state.email = email.strip().lower()
            st.session_state.platform = platform
            st.session_state.active_thread_id = None
            st.rerun()


# -------------------------------------------------------------- chat screen

def _messages_key(thread_id):
    return f"_msgs_{thread_id or 'new'}"


def _flatten(raw_messages):
    # backend stores one row per question+answer pair -- split into two
    # bubbles, keeping the shared message_id/rows/sql/time on the answer
    flat = []
    for row in raw_messages:
        flat.append({"role": "user", "text": row["QUESTION"]})
        flat.append({
            "role": "assistant", "text": row["ANSWER"], "message_id": row["MESSAGE_ID"],
            "rows": row.get("ROWS_JSON") or [], "sql_queries": row.get("SQL_QUERIES_JSON") or [],
            "time_taken_ms": row.get("TIME_TAKEN_MS"),
        })
    return flat


def load_messages(thread_id):
    key = _messages_key(thread_id)
    if key not in st.session_state:
        if thread_id is None:
            st.session_state[key] = []
        else:
            try:
                st.session_state[key] = _flatten(api_get_messages(thread_id))
            except requests.RequestException as e:
                st.error(f"Couldn't load this thread: {e}")
                st.session_state[key] = []
    return st.session_state[key]


def render_sidebar():
    with st.sidebar:
        st.markdown(f"**{st.session_state.email}**")
        st.caption(f"Platform: {st.session_state.platform}")

        if st.button("← Back", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        if st.button("+ New chat", use_container_width=True):
            st.session_state.active_thread_id = None
            st.rerun()

        st.divider()

        try:
            threads = api_get_threads()
        except requests.RequestException as e:
            st.error(f"Couldn't load threads: {e}")
            threads = []

        for t in sorted(threads, key=lambda t: t.get("UPDATED_AT") or 0, reverse=True):
            tid = t["THREAD_ID"]
            title = (t.get("THREAD_TITLE") or "New chat")[:40]
            col1, col2 = st.columns([4, 1])
            with col1:
                active = st.session_state.active_thread_id == tid
                if st.button(title, key=f"t_{tid}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.active_thread_id = tid
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_t_{tid}"):
                    api_delete_thread(tid)
                    st.session_state.pop(_messages_key(tid), None)
                    if st.session_state.active_thread_id == tid:
                        st.session_state.active_thread_id = None
                    st.rerun()


def render_message(m):
    with st.chat_message(m["role"]):
        st.write(m["text"])
        if m["role"] != "assistant":
            return

        col1, col2, col3, _ = st.columns([1, 1, 1, 4])
        with col1:
            if m.get("time_taken_ms") is not None:
                try:
                    seconds = float(m["time_taken_ms"]) / 1000
                    st.caption(f"⏱ {seconds:.1f}s")
                except (TypeError, ValueError):
                    pass
        with col2:
            if m.get("rows") or m.get("sql_queries"):
                with st.popover("🔍"):
                    if m.get("sql_queries"):
                        st.markdown("**SQL**")
                        for q in m["sql_queries"]:
                            st.code(q, language="sql")
                    if m.get("rows"):
                        st.markdown(f"**Rows ({len(m['rows'])})**")
                        st.dataframe(m["rows"], use_container_width=True, hide_index=True)
        with col3:
            if st.button("🗑️", key=f"del_m_{m['message_id']}"):
                api_delete_message(m["message_id"])
                # deleting one message removes the whole Q+A pair server-side --
                # simplest correct thing to do is just refetch the thread fresh
                st.session_state.pop(_messages_key(st.session_state.active_thread_id), None)
                st.rerun()


def render_chat():
    thread_id = st.session_state.active_thread_id
    messages = load_messages(thread_id)

    chat_box = st.container(height=520, border=True)
    with chat_box:
        if not messages:
            st.caption("Start a new conversation below.")
        for m in messages:
            render_message(m)

    prompt = st.chat_input("Ask a question...")
    if prompt:
        messages.append({"role": "user", "text": prompt})
        with chat_box:
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = api_ask(prompt, thread_id)
                    except requests.RequestException as e:
                        st.error(f"Request failed: {e}")
                        return

        new_thread_id = result["thread_id"]
        if thread_id is None and new_thread_id:
            st.session_state[_messages_key(new_thread_id)] = st.session_state.pop(_messages_key(None))
            st.session_state.active_thread_id = new_thread_id

        target_key = _messages_key(new_thread_id)
        st.session_state[target_key].append({
            "role": "assistant", "text": result["answer"], "message_id": result.get("message_id"),
            "rows": result.get("rows") or [], "sql_queries": result.get("sql_queries") or [],
            "time_taken_ms": result.get("time_taken_ms"),
        })
        st.rerun()


# ------------------------------------------------------------------- main

if "email" not in st.session_state:
    render_login()
else:
    render_sidebar()
    render_chat()