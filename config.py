"""
Central configuration for the HR IQ Streamlit front end.

PASS 2 (current): wired to the real Azure backend. There's no "who am I"
endpoint on the backend, so the frontend only ever knows the caller's
email + session token -- never their name, RBAC tier, or manager. That's
why the UI doesn't show a role badge/tier-colored theme anymore; see
README for the small GET /me endpoint that would unlock that later.
"""
import os

API_BASE_URL = os.environ.get(
    "HR_IQ_API_BASE_URL",
    "https://app-hr-iq-api-agc2geabasa5g2fx.westus2-01.azurewebsites.net",
)

APP_NAME = "HR IQ"
APP_TAGLINE = "Agentic HR Assistant"
ACCENT = "#4F46E5"