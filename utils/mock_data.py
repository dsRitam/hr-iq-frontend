"""
Sample data for PASS 1 (UI-only) review. None of this is fetched from
Snowflake or Azure yet -- it exists purely so every screen has something
believable to render. Swapped for real API responses in pass 2.
"""
from config import (
    ACCESS_LEVEL_SELF_ONLY,
    ACCESS_LEVEL_SELF_AND_TEAM,
    ACCESS_LEVEL_HR_FULL,
)

# Demo accounts for the mock login screen (pass 1 only).
# These line up with personas already used to test the real backend, so the
# same three logins will make sense again once pass 2 is wired up.
DEMO_USERS = {
    "rahul@kpipartners.com": {
        "password": "demo1234",
        "name": "Rahul Verma",
        "access_level": ACCESS_LEVEL_SELF_ONLY,
        "title": "Software Engineer",
        "manager": "Vikram Singh",
    },
    "vikram@kpipartners.com": {
        "password": "demo1234",
        "name": "Vikram Singh",
        "access_level": ACCESS_LEVEL_SELF_AND_TEAM,
        "title": "Engineering Manager",
    },
    "ritam@kpipartners.com": {
        "password": "demo1234",
        "name": "Ritam Mondal",
        "access_level": ACCESS_LEVEL_HR_FULL,
        "title": "HR Business Partner",
    },
}

# KPI summary cards, varied by tier -- deliberately simple counts, nothing
# that implies a real proactive-monitoring agent (that part of the reference
# screenshot isn't feasible yet; see README "What we skipped").

KPI_CARDS_BY_TIER = {
    ACCESS_LEVEL_SELF_ONLY: [
        {"label": "Open conversations", "value": "2"},
        {"label": "Leave balance", "value": "6 days"},
        {"label": "Pending goals", "value": "1"},
    ],
    ACCESS_LEVEL_SELF_AND_TEAM: [
        {"label": "Team members", "value": "7"},
        {"label": "Open conversations", "value": "4"},
        {"label": "Reviews due this month", "value": "3"},
    ],
    ACCESS_LEVEL_HR_FULL: [
        {"label": "Employees", "value": "495"},
        {"label": "Open conversations", "value": "11"},
        {"label": "Policy documents indexed", "value": "12"},
    ],
}

# Recent-activity feed, varied by tier. Static/sample only -- the live
# "agent scans continuously" behaviour from the reference screenshot is not
# built yet.
ACTIVITY_FEED_BY_TIER = {
    ACCESS_LEVEL_SELF_ONLY: [
        {"title": "You asked about your leave balance", "when": "Yesterday"},
        {"title": "Goal 'Q3 certification' marked in progress", "when": "3 days ago"},
    ],
    ACCESS_LEVEL_SELF_AND_TEAM: [
        {"title": "You asked which of your reports are due a review", "when": "Today"},
        {"title": "Compared team compensation to department average", "when": "2 days ago"},
    ],
    ACCESS_LEVEL_HR_FULL: [
        {"title": "Queried company-wide attrition by department", "when": "Today"},
        {"title": "Searched policy documents for leave carry-over rules", "when": "Yesterday"},
        {"title": "Reviewed promotion-readiness candidates", "when": "2 days ago"},
    ],
}

# Sample chat threads for the sidebar in the chat view (mirrors screenshot 2).

SAMPLE_THREADS = [
    {"id": "t1", "when": "02:35"},
    {"id": "t2", "when": "Yesterday"},
    {"id": "t3", "when": "2 days ago"},
]

# Placeholder query/result-set shown behind "View query & rows" until pass 2
# wires this up to the real sql_queries/rows the backend already returns.
MOCK_SQL_QUERY = """SELECT e.employee_id, e.full_name, e.department, e.tenure_years,
       e.compa_ratio, e.performance_rating
FROM V_EMPLOYEE_CURRENT e
WHERE e.tenure_years > 3
  AND e.performance_rating >= 4
  AND e.compa_ratio < (
      SELECT AVG(compa_ratio) FROM V_EMPLOYEE_CURRENT d
      WHERE d.department = e.department
  )
ORDER BY e.compa_ratio ASC;"""

MOCK_ROWS = [
    {"employee_id": "E10231", "full_name": "Priya Sharma", "department": "Delivery", "tenure_years": 4.2, "compa_ratio": 0.87},
    {"employee_id": "E10456", "full_name": "Arjun Nair", "department": "Delivery", "tenure_years": 3.6, "compa_ratio": 0.91},
    {"employee_id": "E10788", "full_name": "Sneha Reddy", "department": "Enablement", "tenure_years": 5.1, "compa_ratio": 0.89},
]



SAMPLE_MESSAGES = {
    "t1": [{
            "role": "user",
            "text": (
                "Identify employees who may be ready for promotion by finding those "
                "with more than three years of tenure, consistently high performance "
                "ratings, completed goals, and compensation below the department's "
                "average Compa Ratio. Does any employee require any immediate HR "
                "action? If yes, explain why using supporting records."
            ),
        },
        {
            "role": "assistant",
            "text": (
                "This is a live preview only -- once connected, this is where the "
                "agent's real, RBAC-filtered answer will stream in."
            ),
            "sql_queries": [MOCK_SQL_QUERY],
            "rows": MOCK_ROWS,
            "time_taken_ms": 1840,
        }, ],
    "t2": [
        {"role": "user", "text": "Who on my team has unused leave?"},
        {
            "role": "assistant",
            "text": "This is a UI preview response -- the real answer will appear here once connected.",
            "sql_queries": [MOCK_SQL_QUERY],
            "rows": MOCK_ROWS,
            "time_taken_ms": 1210,
        },
    ],
    "t3": [
        {"role": "user", "text": "Compensation vs department average"},
        {
            "role": "assistant",
            "text": "This is a UI preview response -- the real answer will appear here once connected.",
            "sql_queries": [MOCK_SQL_QUERY],
            "rows": MOCK_ROWS,
            "time_taken_ms": 980,
        },
    ],
}