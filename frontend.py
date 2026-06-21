from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"
LEAVE_TYPES = ["earned", "sick", "casual", "unpaid"]
STATUSES = ["all", "pending", "approved", "rejected"]

st.set_page_config(page_title="LeaveFlow Pro", page_icon="LV", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #f4f7fb;
        color: #172033;
    }
    [data-testid="stSidebar"] {
        background: #101827;
        border-right: 1px solid #1f2937;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }
    .hero {
        padding: 24px 30px;
        border-radius: 8px;
        background: linear-gradient(120deg, #0f766e 0%, #1d4ed8 58%, #b45309 100%);
        color: white;
        margin: 8px 0 22px 0;
        box-shadow: 0 18px 38px rgba(15, 23, 42, 0.16);
    }
    .hero h1 {
        font-size: 34px;
        line-height: 1.15;
        margin: 0 0 8px 0;
        letter-spacing: 0;
    }
    .hero p {
        font-size: 16px;
        margin: 0;
        opacity: 0.94;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 8px;
        padding: 18px;
        min-height: 112px;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.07);
    }
    .metric-card small {
        color: #64748b;
        display: block;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
    }
    .metric-card h2 {
        color: #0f172a;
        font-size: 34px;
        margin: 10px 0 0 0;
    }
    .balance-box {
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        background: #172033;
    }
    .balance-box small {
        color: #cbd5e1;
        display: block;
        font-weight: 700;
    }
    .balance-box b {
        color: #ffffff;
        display: block;
        font-size: 24px;
        margin-top: 4px;
    }
    .profile-line {
        color: #cbd5e1;
        display: block;
        font-size: 13px;
        margin: 5px 0;
        word-break: break-word;
    }
    .status-pill {
        border-radius: 999px;
        display: inline-block;
        font-size: 12px;
        font-weight: 800;
        padding: 5px 10px;
        background: #dbeafe;
        color: #1e40af;
    }
    .clean-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border: 1px solid #e3e8ef;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    }
    .clean-table th {
        background: #eaf1f8;
        color: #334155;
        font-size: 12px;
        text-align: left;
        text-transform: uppercase;
        padding: 12px;
    }
    .clean-table td {
        border-top: 1px solid #e8edf3;
        color: #172033;
        padding: 12px;
    }
    .clean-table tr:nth-child(even) td {
        background: #f8fafc;
    }
    div.stButton > button,
    div.stFormSubmitButton > button,
    div[data-testid="stFormSubmitButton"] button,
    div.stDownloadButton > button {
        border-radius: 8px;
        border: 0;
        background: #0f766e;
        color: #0f172a;
        font-weight: 800;
    }
    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover,
    div.stDownloadButton > button:hover {
        background: #115e59;
        color: #0f172a;
    }
    div.stButton > button p,
    div.stFormSubmitButton > button p,
    div[data-testid="stFormSubmitButton"] button p,
    div.stDownloadButton > button p {
        color: #0f172a !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-baseweb="select"] > div {
        background: #eef7ff !important;
        color: #0f172a !important;
        border: 1px solid #bfdbfe !important;
        border-radius: 8px !important;
    }
    div[role="radiogroup"] label,
    div[role="radiogroup"] p {
        color: #0f172a !important;
        font-weight: 700;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stRadio"] label {
        color: #223047;
        font-weight: 800;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .status-pill {
        background: #dbeafe;
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"],
    [data-testid="stSidebar"] div[role="radiogroup"] *,
    [data-testid="stSidebar"] div[data-testid="stRadio"],
    [data-testid="stSidebar"] div[data-testid="stRadio"] *,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] label *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] div[role="radio"] {
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path, **params):
    response = requests.get(f"{API_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def api_post(path, payload):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def api_patch(path, payload):
    response = requests.patch(f"{API_URL}{path}", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def api_delete(path):
    response = requests.delete(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def readable_error(exc):
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            detail = response.json().get("detail")
            if detail:
                return detail
        except Exception:
            pass
    return str(exc)


def flash_success():
    message = st.session_state.pop("success_message", None)
    if message:
        st.success(message)


def set_success(message):
    st.session_state.success_message = message


def show_hero(user):
    st.markdown(
        f"""
        <div class="hero">
            <h1>LeaveFlow Pro</h1>
            <p>Welcome, <b>{user["name"]}</b>. Your {user["role"].title()} dashboard is ready.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <small>{label}</small>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clean_table(items, columns=None):
    if not items:
        st.info("No records found.")
        return
    data = pd.DataFrame(items)
    if columns:
        data = data[[col for col in columns if col in data.columns]]
    st.markdown(data.to_html(index=False, classes="clean-table", escape=False), unsafe_allow_html=True)


def chart_from_dict(title, values):
    st.subheader(title)
    if not values:
        st.info("No chart data available.")
        return
    data = pd.DataFrame([{"category": key, "days": value} for key, value in values.items()])
    st.bar_chart(data, x="category", y="days", width="stretch")


def compact_bar_chart(title, rows, label_column, value_column):
    st.subheader(title)
    if not rows:
        st.info("No chart data available.")
        return
    data = pd.DataFrame(rows)
    max_value = float(data[value_column].max()) or 1
    html = ['<div style="background:white;border:1px solid #e3e8ef;border-radius:8px;padding:14px;">']
    for _, row in data.iterrows():
        value = float(row[value_column])
        width = max(6, int((value / max_value) * 100))
        html.append(
            f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;color:#0f172a;font-weight:700;font-size:13px;">
                    <span>{row[label_column]}</span><span>{value:g}</span>
                </div>
                <div style="height:10px;background:#eaf1f8;border-radius:999px;margin-top:6px;overflow:hidden;">
                    <div style="height:10px;width:{width}%;background:#0f766e;border-radius:999px;"></div>
                </div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def next_working_day(start):
    holidays = {item["holiday_date"] for item in api_get("/holidays")}
    current = start
    while current.weekday() >= 5 or current.isoformat() in holidays:
        current += timedelta(days=1)
    return current


def estimated_working_days(start_date, end_date, day_mode):
    holidays = {item["holiday_date"] for item in api_get("/holidays")}
    if end_date < start_date:
        return 0
    total = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current.isoformat() not in holidays:
            total += 1
        current += timedelta(days=1)
    if day_mode == "half":
        return 0.5 if start_date == end_date and total == 1 else 0
    return float(total)


def filter_requests(items, managers=True):
    if not items:
        return []
    data = pd.DataFrame(items)
    col1, col2, col3 = st.columns(3)
    with col1:
        status = st.selectbox("Status", STATUSES)
    with col2:
        leave_type = st.selectbox("Leave type", ["all"] + sorted(data["leave_type"].dropna().unique().tolist()))
    with col3:
        if managers and "manager" in data.columns:
            manager = st.selectbox("Manager", ["all"] + sorted(data["manager"].fillna("-").unique().tolist()))
        else:
            manager = "all"

    filtered = data.copy()
    if status != "all":
        filtered = filtered[filtered["status"] == status]
    if leave_type != "all":
        filtered = filtered[filtered["leave_type"] == leave_type]
    if manager != "all":
        filtered = filtered[filtered["manager"].fillna("-") == manager]
    return filtered.to_dict("records")


def login_screen():
    left, middle, right = st.columns([1, 1.05, 1])
    with middle:
        st.markdown(
            """
            <div class="hero">
                <h1>LeaveFlow Pro</h1>
                <p>Role-based leave management for employees, managers, and HR admins.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.subheader("Sign in")
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", value="123", type="password")
            st.caption("Demo users: admin / 123, manager / 123, employee / 123")

            if st.button("Login", width="stretch"):
                try:
                    st.session_state.user = api_post("/login", {"username": username, "password": password})
                    set_success("Login successful.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Login failed: {exc}")


def user_by_username(username):
    users = api_get("/employees")
    return next((item for item in users if item["username"] == username), None)


def show_sidebar_profile(user):
    fresh_user = user_by_username(user["username"]) or user
    manager_name = "-"
    if fresh_user.get("manager"):
        manager = user_by_username(fresh_user["manager"])
        manager_name = manager["name"] if manager else fresh_user["manager"]

    st.markdown(f"<span class='profile-line'><b>Emp ID:</b> {fresh_user.get('emp_id', '-')}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='profile-line'><b>Email:</b> {fresh_user.get('email', '-')}</span>", unsafe_allow_html=True)
    if fresh_user["role"] == "employee":
        st.markdown(f"<span class='profile-line'><b>Manager:</b> {manager_name}</span>", unsafe_allow_html=True)
    return fresh_user


def show_leave_balances(username):
    balances = api_get(f"/employees/{username}/balances")
    st.markdown("### Leave Balance")
    labels = [("earned", "Earned Leave"), ("sick", "Sick Leave"), ("casual", "Casual Leave")]
    for key, label in labels:
        st.markdown(
            f"""
            <div class="balance-box">
                <small>{label}</small>
                <b>{balances.get(key, 0):g}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


def employee_dashboard(user):
    balances = api_get(f"/employees/{user['username']}/balances")
    requests_data = api_get("/leave", username=user["username"], role=user["role"])
    holidays = api_get("/holidays")
    page = st.session_state.get("employee_page", "Apply Leave")

    cols = st.columns(3)
    for col, leave_type in zip(cols, ["earned", "sick", "casual"]):
        with col:
            metric_card(f"{leave_type.title()} Leave", f"{balances.get(leave_type, 0):g}")

    if page == "Apply Leave":
        default_date = next_working_day(date.today())
        with st.form("employee_leave_form", clear_on_submit=True):
            st.subheader("Input Details")
            col1, col2 = st.columns(2)
            with col1:
                leave_type = st.selectbox("Leave type", LEAVE_TYPES)
                start_date = st.date_input("Start date", value=default_date, min_value=date.today())
                day_mode = st.radio(
                    "Leave duration",
                    ["full", "half"],
                    format_func=lambda value: "Full Day" if value == "full" else "Half Day",
                    horizontal=True,
                )
            with col2:
                end_date = st.date_input("End date", value=default_date, min_value=date.today())
                reason = st.text_area("Reason", placeholder="Add a short reason for your manager")

            estimated_days = 0.5 if day_mode == "half" else estimated_working_days(start_date, end_date, day_mode)
            st.info(f"Estimated leave days: {estimated_days:g}")

            if st.form_submit_button("Submit request", width="stretch"):
                if estimated_days <= 0:
                    st.error("Please select a valid working day. Weekends and holidays are not counted.")
                    return
                try:
                    api_post(
                        "/leave",
                        {
                            "username": user["username"],
                            "leave_type": leave_type,
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "day_mode": day_mode,
                            "reason": reason,
                        },
                    )
                    set_success("Leave request submitted and balance deducted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not submit request: {readable_error(exc)}")

    elif page == "Leave History":
        filtered = filter_requests(requests_data, managers=False)
        clean_table(filtered, ["id", "leave_type", "start_date", "end_date", "day_mode", "days", "reason", "status", "comments"])

    elif page == "Holiday Calendar":
        st.subheader("2026 Holiday Calendar")
        st.date_input("Open calendar", value=date.today())
        clean_table(holidays, ["name", "holiday_date"])


def manager_dashboard(user):
    team_requests = api_get("/leave", username=user["username"], role=user["role"])
    holidays = api_get("/holidays")
    page = st.session_state.get("manager_page", "Dashboard")
    pending = [item for item in team_requests if item["status"] == "pending"]
    approved = [item for item in team_requests if item["status"] == "approved"]
    rejected = [item for item in team_requests if item["status"] == "rejected"]

    if page == "Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Pending Queue", len(pending))
        with c2:
            metric_card("Approved", len(approved))
        with c3:
            metric_card("Rejected", len(rejected))
        with c4:
            metric_card("Team Leave Days", f"{sum(item['days'] for item in team_requests):g}")

        if team_requests:
            data = pd.DataFrame(team_requests)
            col1, col2 = st.columns(2)
            with col1:
                compact_bar_chart(
                    "Team leave by status",
                    data.groupby("status")["days"].sum().reset_index().to_dict("records"),
                    "status",
                    "days",
                )
            with col2:
                compact_bar_chart(
                    "Team leave by type",
                    data.groupby("leave_type")["days"].sum().reset_index().to_dict("records"),
                    "leave_type",
                    "days",
                )
        else:
            st.info("No team leave data available.")

    elif page == "Approve/Reject":
        if not pending:
            st.success("No pending requests.")
        for item in pending:
            with st.container(border=True):
                st.markdown(
                    f"**{item['employee_name']}** requested **{item['days']:g} day(s)** of "
                    f"**{item['leave_type']}** leave from `{item['start_date']}` to `{item['end_date']}`."
                )
                st.caption(item["reason"])
                comments = st.text_input("Manager comments", key=f"comments_{item['id']}")
                col1, col2, _ = st.columns([1, 1, 4])
                with col1:
                    if st.button("Approve", key=f"approve_{item['id']}"):
                        api_patch(
                            f"/leave/{item['id']}/decision",
                            {"manager_username": user["username"], "status": "approved", "comments": comments},
                        )
                        set_success("Leave request approved.")
                        st.rerun()
                with col2:
                    if st.button("Reject", key=f"reject_{item['id']}"):
                        api_patch(
                            f"/leave/{item['id']}/decision",
                            {"manager_username": user["username"], "status": "rejected", "comments": comments},
                        )
                        set_success("Leave request rejected and balance restored.")
                        st.rerun()

    elif page == "Reports":
        filtered = filter_requests(team_requests, managers=False)
        clean_table(filtered, ["id", "employee_name", "leave_type", "day_mode", "days", "status", "comments"])
        if filtered:
            data = pd.DataFrame(filtered)
            col1, col2 = st.columns(2)
            with col1:
                compact_bar_chart(
                    "Filtered leave by status",
                    data.groupby("status")["days"].sum().reset_index().to_dict("records"),
                    "status",
                    "days",
                )
            with col2:
                compact_bar_chart(
                    "Filtered leave by type",
                    data.groupby("leave_type")["days"].sum().reset_index().to_dict("records"),
                    "leave_type",
                    "days",
                )

    elif page == "Holiday Calendar":
        st.subheader("2026 Holiday Calendar")
        st.date_input("Open calendar", value=date.today())
        clean_table(holidays, ["name", "holiday_date"])


def admin_overview():
    employees = api_get("/employees/table")
    all_requests = api_get("/leave", username="admin", role="admin")
    report = api_get("/reports/summary")
    org = api_get("/reports/organization")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Employees", org["employees"])
    with c2:
        metric_card("Managers", org["managers"])
    with c3:
        metric_card("Total Strength", org["total_strength"])
    with c4:
        metric_card("Leave Requests", report["total_requests"])

    col1, col2 = st.columns(2)
    with col1:
        chart_from_dict("Leave days by status", report["leave_days_by_status"])
    with col2:
        chart_from_dict("Leave days by manager", report["leave_days_by_manager"])

    st.subheader("Leave report")
    filtered = filter_requests(all_requests)
    clean_table(filtered, ["id", "employee_name", "department", "manager", "leave_type", "day_mode", "days", "status", "comments"])
    if filtered:
        csv = pd.DataFrame(filtered).to_csv(index=False).encode("utf-8")
        st.download_button("Export filtered report", csv, "leave_report.csv", "text/csv", width="stretch")

    st.subheader("Organisation directory")
    clean_table(employees)


def admin_add_user():
    employees = api_get("/employees")
    managers = [item for item in employees if item["role"] == "manager"]
    manager_names = [item["username"] for item in managers]

    with st.form("add_user_form", clear_on_submit=True):
        st.subheader("Input Details")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            name = st.text_input("Full name")
            email = st.text_input("Email ID")
            department = st.text_input("Department", value="Engineering")
        with col2:
            role = st.selectbox("Role", ["employee", "manager", "admin"])
            if role == "manager":
                manager = st.text_input("Assigned manager", value="admin", disabled=True)
            elif role == "admin":
                manager = None
                st.text_input("Assigned manager", value="-", disabled=True)
            else:
                manager = st.selectbox("Assigned manager", manager_names or ["admin"])

            earned = st.number_input("Earned leave", min_value=0.0, value=10.0, step=0.5)
            sick = st.number_input("Sick leave", min_value=0.0, value=12.0, step=0.5)
            casual = st.number_input("Casual leave", min_value=0.0, value=6.0, step=0.5)

        if st.form_submit_button("Add user", width="stretch"):
            try:
                created = api_post(
                    "/employees",
                    {
                        "username": username,
                        "password": password,
                        "name": name,
                        "email": email,
                        "department": department,
                        "role": role,
                        "manager": manager,
                        "earned_balance": earned,
                        "sick_balance": sick,
                        "casual_balance": casual,
                    },
                )
                set_success(f"User added successfully. Employee ID: {created['emp_id']}")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not add user: {readable_error(exc)}")


def admin_manage_users():
    employees = api_get("/employees")
    employee_table = api_get("/employees/table")
    usernames = [item["username"] for item in employees]
    selected = st.selectbox("Select user", usernames)
    user = next(item for item in employees if item["username"] == selected)
    managers = [item["username"] for item in employees if item["role"] == "manager"]

    clean_table(employee_table)

    with st.form("manage_user_form", clear_on_submit=False):
        st.subheader("Manage User Details")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Employee ID", value=user["emp_id"], disabled=True)
            name = st.text_input("Full name", value=user["name"])
            email = st.text_input("Email ID", value=user["email"])
            department = st.text_input("Department", value=user["department"])
            role = st.selectbox("Role", ["employee", "manager", "admin"], index=["employee", "manager", "admin"].index(user["role"]))
        with col2:
            if role == "manager":
                manager = st.text_input("Assigned manager", value="admin", disabled=True)
            elif role == "admin":
                manager = None
                st.text_input("Assigned manager", value="-", disabled=True)
            else:
                current_manager = user["manager"] if user["manager"] in managers else (managers[0] if managers else "admin")
                manager = st.selectbox("Assigned manager", managers or ["admin"], index=(managers or ["admin"]).index(current_manager))

            balances = user["balances"]
            earned = st.number_input("Earned leave", min_value=0.0, value=float(balances["earned"]), step=0.5)
            sick = st.number_input("Sick leave", min_value=0.0, value=float(balances["sick"]), step=0.5)
            casual = st.number_input("Casual leave", min_value=0.0, value=float(balances["casual"]), step=0.5)
            new_password = st.text_input("Reset password", type="password", placeholder="Leave blank to keep existing password")

        if st.form_submit_button("Update user", width="stretch"):
            try:
                api_patch(
                    f"/employees/{selected}",
                    {
                        "name": name,
                        "email": email,
                        "department": department,
                        "role": role,
                        "manager": manager,
                        "earned_balance": earned,
                        "sick_balance": sick,
                        "casual_balance": casual,
                        "new_password": new_password or None,
                    },
                )
                set_success("User details updated successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not update user: {readable_error(exc)}")


def admin_delete_user():
    st.markdown(
        """
        <style>
        div.stButton > button {
            background: #dc2626 !important;
            color: white !important;
        }
        div.stButton > button:hover {
            background: #b91c1c !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    employees = [item for item in api_get("/employees") if item["username"] != "admin"]
    if not employees:
        st.info("No users available for deletion.")
        return

    st.subheader("Delete User")
    selected = st.selectbox("Select user to delete", [item["username"] for item in employees])
    user = next(item for item in employees if item["username"] == selected)
    clean_table(
        [
            {
                "emp_id": user["emp_id"],
                "username": user["username"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "manager": user["manager"] or "-",
            }
        ]
    )
    if st.button("Delete user", width="stretch"):
        try:
            api_delete(f"/employees/{selected}")
            set_success(f"{selected} deleted successfully.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not delete user: {readable_error(exc)}")


def admin_manager_mapping():
    org = api_get("/reports/organization")
    managers = list(org["manager_mapping"].keys())
    if not managers:
        st.info("No employee-manager mappings found.")
        return

    selected_manager = st.selectbox("Select manager", managers)
    st.subheader(f"Employees mapped to {selected_manager}")
    clean_table(org["manager_mapping"].get(selected_manager, []))


def admin_holidays():
    col1, col2 = st.columns([1, 1.6])
    with col1:
        with st.form("holiday_form", clear_on_submit=True):
            st.subheader("Input Details")
            name = st.text_input("Holiday name")
            holiday_date = st.date_input("Holiday date")
            if st.form_submit_button("Add holiday", width="stretch"):
                try:
                    api_post("/holidays", {"name": name, "holiday_date": str(holiday_date)})
                    set_success("Holiday added successfully.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not add holiday: {exc}")
    with col2:
        st.subheader("Holiday list for 2026")
        clean_table(api_get("/holidays"), ["name", "holiday_date"])


def admin_dashboard():
    page = st.session_state.get("admin_page", "Dashboard")
    if page == "Dashboard":
        admin_overview()
    elif page == "Add User":
        admin_add_user()
    elif page == "Manage User Details":
        admin_manage_users()
    elif page == "Delete User":
        admin_delete_user()
    elif page == "Manager Mapping":
        admin_manager_mapping()
    elif page == "Holidays":
        admin_holidays()


def sidebar(user):
    with st.sidebar:
        st.title("LeaveFlow")
        st.markdown(f"<span class='status-pill'>{user['role'].title()}</span>", unsafe_allow_html=True)
        st.write(user["name"])

        if user["role"] == "admin":
            st.divider()
            previous_page = st.session_state.get("admin_page", "Dashboard")
            page = st.radio(
                "Admin Dashboard",
                ["Dashboard", "Add User", "Manage User Details", "Delete User", "Manager Mapping", "Holidays"],
                label_visibility="visible",
            )
            st.session_state.admin_page = page
            if previous_page != page:
                st.toast(f"{page} opened successfully.")
        else:
            st.divider()
            fresh_user = show_sidebar_profile(user)
            st.divider()
            if user["role"] == "manager":
                previous_page = st.session_state.get("manager_page", "Dashboard")
                page = st.radio(
                    "Manager Dashboard",
                    ["Dashboard", "Reports", "Approve/Reject", "Holiday Calendar"],
                    label_visibility="visible",
                )
                st.session_state.manager_page = page
                if previous_page != page:
                    st.toast(f"{page} opened successfully.")
            else:
                previous_page = st.session_state.get("employee_page", "Apply Leave")
                page = st.radio(
                    "Employee Dashboard",
                    ["Apply Leave", "Leave History", "Holiday Calendar"],
                    label_visibility="visible",
                )
                st.session_state.employee_page = page
                if previous_page != page:
                    st.toast(f"{page} opened successfully.")
            st.divider()
            show_leave_balances(fresh_user["username"])

        st.divider()
        if st.button("Logout", width="stretch"):
            st.session_state.clear()
            st.rerun()


def main():
    if "user" not in st.session_state:
        login_screen()
        return

    user = st.session_state.user
    sidebar(user)
    show_hero(user)
    flash_success()

    if user["role"] == "admin":
        admin_dashboard()
    elif user["role"] == "manager":
        manager_dashboard(user)
    else:
        employee_dashboard(user)


if __name__ == "__main__":
    main()
