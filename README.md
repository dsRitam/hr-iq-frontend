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


