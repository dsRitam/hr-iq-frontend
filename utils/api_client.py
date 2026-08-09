"""
Talks to the real HR IQ FastAPI backend on Azure. Views never call
`requests` directly -- everything goes through here, matched exactly to
main.py / chat_history.py as they exist today:

  POST   /auth/register  {email, password}            -> {status, email}
  POST   /auth/login     {email, password}             -> {token}
  POST   /ask            {question, thread_id?}         -> SSE stream
         events: step, sql, answer_delta, done, error
  GET    /threads                                        -> {threads: [...]}
  GET    /threads/{thread_id}/messages                    -> {thread_id, messages: [...]}
  DELETE /threads/{thread_id}                               -> {status, thread_id}
  DELETE /messages/{message_id}                              -> {status, message_id}

All authenticated routes take `Authorization: Bearer <token>`. There is no
"who am I" endpoint -- resolve_access_scope() runs server-side only, so the
frontend never learns the caller's name / RBAC tier / manager. Anything
that would need that (a role badge, a manager name, an RBAC-tinted theme)
had to come out of the UI for this pass; see the app's README for the
follow-up suggestion (a small GET /me endpoint) if that's wanted later.
"""
import json

import requests

from config import API_BASE_URL

DEFAULT_TIMEOUT = 20
ASK_TIMEOUT = (10, 180)  # (connect, read) -- generous read timeout for a live agent call


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _headers(token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _raise_for_status(resp: requests.Response):
    if resp.status_code >= 400:
        detail = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        raise ApiError(detail or f"Request failed ({resp.status_code}).", status_code=resp.status_code)


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """Wraps requests.<method> so a DNS failure / connection refused /
    timeout comes back as an ApiError like any other failure, instead of
    an uncaught requests exception reaching the UI."""
    try:
        resp = requests.request(method, url, **kwargs)
    except requests.RequestException as e:
        raise ApiError(f"Couldn't reach the server: {e}")
    _raise_for_status(resp)
    return resp


def register(email: str, password: str) -> dict:
    """POST /auth/register. Note: the backend only accepts email+password --
    it doesn't create a new employee, it just sets a password for an email
    that must already exist in EMPLOYEE_ACCESS_MAP. A 403 here typically
    means that email isn't a recognized employee; a 409 means it's already
    registered."""
    resp = _request(
        "POST",
        f"{API_BASE_URL}/auth/register",
        json={"email": email.strip().lower(), "password": password},
        headers=_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    return resp.json()


def login(email: str, password: str) -> dict:
    """POST /auth/login -> {token}. Returns {email, token} for session state."""
    resp = _request(
        "POST",
        f"{API_BASE_URL}/auth/login",
        json={"email": email.strip().lower(), "password": password},
        headers=_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    token = resp.json()["token"]
    return {"email": email.strip().lower(), "token": token}


def list_threads(token: str) -> list:
    """GET /threads -> list of {THREAD_ID, THREAD_TITLE, CREATED_AT, UPDATED_AT}."""
    resp = _request("GET", f"{API_BASE_URL}/threads", headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    return resp.json().get("threads", [])


def list_messages(token: str, thread_id: str) -> list:
    """GET /threads/{id}/messages -> list of
    {MESSAGE_ID, QUESTION, ANSWER, ROWS_JSON, SQL_QUERIES_JSON, TIME_TAKEN_MS, CREATED_AT}.
    One row per question+answer pair (not separate user/assistant rows)."""
    resp = _request(
        "GET", f"{API_BASE_URL}/threads/{thread_id}/messages", headers=_headers(token), timeout=DEFAULT_TIMEOUT
    )
    return resp.json().get("messages", [])


def delete_thread(token: str, thread_id: str) -> dict:
    resp = _request(
        "DELETE", f"{API_BASE_URL}/threads/{thread_id}", headers=_headers(token), timeout=DEFAULT_TIMEOUT
    )
    return resp.json()


def delete_message(token: str, message_id: str) -> dict:
    resp = _request(
        "DELETE", f"{API_BASE_URL}/messages/{message_id}", headers=_headers(token), timeout=DEFAULT_TIMEOUT
    )
    return resp.json()



def get_my_manager(token: str) -> dict:
    """GET /me/manager -> {manager_employee_id, manager_name} (both null if
    the caller has no manager -- e.g. top of the org)."""
    resp = _request("GET", f"{API_BASE_URL}/me/manager", headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    return resp.json()


def get_my_leaves_taken(token: str) -> dict:
    """GET /me/leaves-taken-this-year -> {leave_requests_this_year, total_days_this_year}."""
    resp = _request(
        "GET", f"{API_BASE_URL}/me/leaves-taken-this-year", headers=_headers(token), timeout=DEFAULT_TIMEOUT
    )
    return resp.json()


def get_my_goals_due(token: str) -> dict:
    """GET /me/goals-due -> {open_goals_due, overdue_goals}."""
    resp = _request("GET", f"{API_BASE_URL}/me/goals-due", headers=_headers(token), timeout=DEFAULT_TIMEOUT)
    return resp.json()


def stream_ask(token: str, question: str, thread_id: str | None):
    """POST /ask, consumed as Server-Sent Events. Yields dicts:
        {"type": "step" | "sql" | "answer_delta" | "done" | "error", "data": {...}}
    matching main.py's sse_pack() format exactly
    (`event: <type>\\ndata: <json>\\n\\n`). On an HTTP-level failure (bad
    token, 5xx, etc.) yields a single synthetic "error" event instead of
    raising, so callers can handle both the same way.
    """
    payload = {"question": question}
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        resp = requests.post(
            f"{API_BASE_URL}/ask",
            json=payload,
            headers=_headers(token),
            stream=True,
            timeout=ASK_TIMEOUT,
        )
    except requests.RequestException as e:
        yield {"type": "error", "data": {"detail": f"Couldn't reach the server: {e}"}}
        return

    if resp.status_code >= 400:
        detail = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        yield {"type": "error", "data": {"detail": detail, "status_code": resp.status_code}}
        return

    event_type = None
    data_lines: list[str] = []
    try:
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.rstrip("\r")
            if line == "":
                if event_type is not None:
                    yield {"type": event_type, "data": _parse_sse_data(data_lines)}
                event_type, data_lines = None, []
                continue
            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        # A stream that ends without a trailing blank line -- flush whatever's left.
        if event_type is not None and data_lines:
            yield {"type": event_type, "data": _parse_sse_data(data_lines)}
    except requests.RequestException as e:
        yield {"type": "error", "data": {"detail": f"Connection dropped: {e}"}}


def _parse_sse_data(data_lines: list[str]) -> dict:
    data_str = "\n".join(data_lines)
    try:
        return json.loads(data_str) if data_str else {}
    except json.JSONDecodeError:
        return {"raw": data_str}