# HR IQ — Streamlit Front End

A standalone Streamlit project (separate from the FastAPI/Azure backend
repo) that will act as the chat + dashboard UI for employees, managers, and
HR, sitting in front of the existing `app-hr-iq-api` Azure Web App.

**Demo logins**:
| Email | Password | Role |
|---|---|---|
| rahul@kpipartners.com | CONTACT ME | Employee (SELF_ONLY) |
| vikram@kpipartners.com | CONTACT ME | Reporting Manager (SELF_AND_TEAM) |
| ritam@kpipartners.com | CONTACT ME | HR Business Partner (HR_FULL) |


### Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```


