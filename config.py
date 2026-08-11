"""
Central configuration for the HR IQ Streamlit front end.

PASS 2+ : wired to the real Azure backend. There's no "who am I"
endpoint on the backend beyond hr_features_access, so the frontend only
ever knows the caller's email, session token, and whether HR IQ features
specifically are usable -- never their name, RBAC tier, or manager
directly (manager name comes from a separate /me/manager call once
inside the HR IQ workspace). That's why the UI doesn't show a role
badge/tier-colored theme; see README for a fuller GET /me endpoint that
would unlock that later.

Landing-page workspace launcher (added alongside SSO): APPS below drives
the 4-card app-picker page shown after login, before entering any
specific app's workspace.
"""
import os

API_BASE_URL = os.environ.get(
    "HR_IQ_API_BASE_URL",
    "https://app-hr-iq-api-agc2geabasa5g2fx.westus2-01.azurewebsites.net",
)

APP_NAME = "HR IQ"
APP_TAGLINE = "Agentic HR Assistant"
ACCENT = "#4F46E5"

# -- Multi-app workspace launcher --
# Order matches how they appear on the landing page (left to right).
APPS = [
    {
        "id": "procurement_iq",
        "name": "Procurement IQ",
        "tagline": "Agentic assistant for sourcing & vendor spend",
        "icon": "📦",
        "color": "#0EA5E9",
        "real": False,
    },
    {
        "id": "supply_chain_iq",
        "name": "Supply Chain IQ",
        "tagline": "Agentic assistant for inventory & logistics",
        "icon": "🚚",
        "color": "#F59E0B",
        "real": False,
    },
    {
        "id": "sales_iq",
        "name": "Sales IQ",
        "tagline": "Agentic assistant for pipeline & forecasting",
        "icon": "📈",
        "color": "#10B981",
        "real": False,
    },
    {
        "id": "hr_iq",
        "name": "HR IQ",
        "tagline": "Agentic HR assistant for pay, leave, goals & policy",
        "icon": "🧑‍💼",
        "color": ACCENT,
        "real": True,
    },
]