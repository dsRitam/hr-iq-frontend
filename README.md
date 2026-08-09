# HR IQ — Streamlit Front End

A standalone Streamlit project (separate from the FastAPI/Azure backend
repo) that will act as the chat + dashboard UI for employees, managers, and
HR, sitting in front of the existing `app-hr-iq-api` Azure Web App.

## Where this stands right now — Pass 1 (UI only)

`MOCK_MODE` is on. There are **no network calls** to the Azure backend yet.
Login, register, the dashboard KPIs, and chat responses are all backed by
`utils/mock_data.py` / in-memory session state, purely so the look and flow
can be reviewed before wiring anything up.

**Demo logins** (see `utils/mock_data.py`):
| Email | Password | Role |
|---|---|---|
| rahul@kpipartners.com | demo1234 | Employee (SELF_ONLY) |
| vikram@kpipartners.com | demo1234 | Reporting Manager (SELF_AND_TEAM) |
| ritam@kpipartners.com | demo1234 | HR Business Partner (HR_FULL) |

Register creates a session-only account (not persisted) so you can preview
that flow too.

### Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Structure

```
app.py                 # entry point — gates navigation on auth state
config.py               # API base URL, mock-mode flag, RBAC tier constants/colors
views/
  auth.py               # login + register (tabs)
  dashboard.py           # KPI cards + recent-activity feed, role-aware
  chat.py                 # chat history sidebar + conversation, mirrors HR IQ chat UI
utils/
  state.py               # session-state helpers (auth gating)
  api_client.py            # ALL backend calls go through here — mocked for now
  mock_data.py              # sample users / KPIs / threads / messages
.streamlit/config.toml       # theme
```

The RBAC tier names (`SELF_ONLY` / `SELF_AND_TEAM` / `HR_FULL`) in
`config.py` match `EMPLOYEE_ACCESS_MAP.ACCESS_LEVEL` in Snowflake, so the
same three demo personas carry straight through to pass 2.

## What we adapted from the reference screenshots (and what we skipped)

**Dashboard** (screenshot 1, "HR IQ — Agentic Command Center"): kept the
top KPI-card row and a recent-activity feed, restyled per role. Skipped for
now, as not feasible in this pass:
- The live "agent active · monitoring N employees · last scan just now"
  status bar — that implies a background monitoring job we haven't built.
- Per-insight AI recommendations with inline actions ("Approve & send
  reminder", "Ask a follow-up", confidence %) — those imply a proactive
  detection agent, not the on-demand Q&A agent we have today.
- Three separate persona "agents" (Leave Reconciliation / Employee 360 /
  Payroll Fraud) — we have one agent per RBAC tier, not per task type.

**Chat page** (screenshot 2, "AI HR Agent"): kept the chat-history sidebar
with a "New chat" button and thread list, the persona badge, and the main
conversation panel with a bottom input. This lines up directly with the
`chat_history.py` module and `/threads`, `/threads/{id}/messages`, `/ask`
endpoints already built on the backend.

## Pass 2 — wiring it to the real backend

Everything that needs to change lives in `utils/api_client.py`:
- `login` / `register` → call whatever auth routes exist against the
  SQLite `app.db` on Azure.
- `list_threads` / `list_messages` → `GET /threads`, `GET /threads/{id}/messages`.
- `ask` → stream `POST /ask` (SSE) and yield deltas into the chat bubble
  instead of the current single mock string.

`API_BASE_URL` in `config.py` already points at the real Azure Web App
(`https://app-hr-iq-api-agc2geabasa5g2fx.westus2-01.azurewebsites.net`),
overridable via the `HR_IQ_API_BASE_URL` env var — set that in Streamlit
Cloud's app settings ("Secrets") rather than hardcoding it, and flip
`HR_IQ_MOCK_MODE=false` once `api_client.py` is filled in.
