import streamlit as st

from config import APPS
from utils import api_client
from utils.state import current_user, enter_app, log_out


def _app_card(app: dict, hr_features_access: bool):
    is_hr = app["id"] == "hr_iq"
    locked = is_hr and not hr_features_access
    coming_soon = not app["real"]

    with st.container(border=True):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">'
            f'<div style="width:40px;height:40px;border-radius:10px;'
            f'background:{app["color"]};color:white;display:flex;align-items:center;'
            f'justify-content:center;font-size:1.3rem;">{app["icon"]}</div>'
            f'<div style="font-weight:700;font-size:1.02rem;">{app["name"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:#6B7280;font-size:0.82rem;min-height:2.4rem;">{app["tagline"]}</p>',
            unsafe_allow_html=True,
        )

        if coming_soon:
            st.button("Coming soon", key=f"enter_{app['id']}", use_container_width=True, disabled=True)
        elif locked:
            st.button(
                "Not available for your account", key=f"enter_{app['id']}",
                use_container_width=True, disabled=True,
            )
            st.caption("Contact HR if you believe this is incorrect.")
        else:
            if st.button(
                "Enter workspace →", key=f"enter_{app['id']}",
                use_container_width=True, type="primary",
            ):
                enter_app(app["id"])
                st.rerun()


def render():
    user = current_user()

    st.markdown(
        '<div style="text-align:center;padding:1.2rem 0 0.4rem 0;">'
        '<div style="font-weight:700;font-size:1.3rem;">Welcome to the KPI Partners Workspace</div>'
        '<div style="color:#6B7280;font-size:0.85rem;margin-top:0.2rem;">'
        'Choose an app to get started</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    # Re-checked fresh on every landing page load, rather than trusting
    # only the value captured at login/SSO time -- this is documented as
    # session-refreshable (e.g. someone could be added to HR IQ access
    # mid-session), not a one-time fact.
    hr_features_access = user.get("hr_features_access", False)
    try:
        hr_features_access = api_client.get_my_hr_features_access(user["token"])
        user["hr_features_access"] = hr_features_access
    except api_client.ApiError as e:
        if e.status_code == 401:
            log_out("Your session expired — please log in again.")
            st.rerun()
        # Any other failure: fall back to whatever we already knew rather
        # than blocking the whole landing page over one flaky check.

    cols = st.columns(4)
    for col, app in zip(cols, APPS):
        with col:
            _app_card(app, hr_features_access)


render()