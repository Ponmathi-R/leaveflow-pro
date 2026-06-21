# leaveflow-pro
 LeaveFlow Pro is a role-based leave management system built with Streamlit, FastAPI, and SQLite. It supports admin, manager, and employee dashboards, leave requests, approvals, balance tracking, holiday calendar, reports, and persistent data storage.

# LeaveFlow Pro

LeaveFlow Pro is a role-based leave management system built with **FastAPI**, **Streamlit**, and **SQLite**. It provides separate dashboards for Admin, Manager, and Employee users, with leave balance tracking, approval workflows, holiday calendars, employee management, reports, and persistent database storage.

## Features

- Role-based login for Admin, Manager, and Employee
- Admin dashboard with employee count, manager count, total strength, charts, and reports
- Add, update, reset password, and delete users
- Auto-generated employee IDs:
  - Managers: `GENAIM1150...`
  - Employees: `GENAIE2650...`
- Manager-to-employee mapping view
- Leave request submission with full-day and half-day support
- Leave balance deduction during request submission
- Leave balance restoration when a request is rejected
- Manager approval and rejection workflow
- 2026 holiday calendar
- SQLite database storage so data is not lost after restart
- Clean professional Streamlit UI

## System Flow Chart

```mermaid
flowchart TD
    A["User opens LeaveFlow Pro"] --> B["Login with username and password"]
    B --> C{"Authenticated?"}
    C -- "No" --> D["Show login error"]
    D --> B
    C -- "Yes" --> E{"User role"}

    E -- "Admin" --> F["Admin Dashboard"]
    F --> F1["Manage users"]
    F --> F2["Manage holidays"]
    F --> F3["View employee-manager mapping"]
    F --> F4["View reports and charts"]
    F1 --> F5["Add, update, reset password, or delete user"]

    E -- "Manager" --> G["Manager Dashboard"]
    G --> G1["View team leave requests"]
    G1 --> G2{"Approve or reject?"}
    G2 -- "Approve" --> G3["Mark request as approved"]
    G2 -- "Reject" --> G4["Mark request as rejected"]
    G4 --> G5["Restore deducted leave balance"]
    G --> G6["View team reports"]
    G --> G7["View holiday calendar"]

    E -- "Employee" --> H["Employee Dashboard"]
    H --> H1["View leave balances"]
    H --> H2["Apply leave"]
    H2 --> H3["Select leave type, dates, and full/half day"]
    H3 --> H4{"Valid working day and balance available?"}
    H4 -- "No" --> H5["Show validation message"]
    H4 -- "Yes" --> H6["Create pending leave request"]
    H6 --> H7["Deduct leave balance immediately"]
    H --> H8["View leave history"]
    H --> H9["View holiday calendar"]

    H7 --> G1
    G3 --> H8
    G5 --> H8
```

## Default Login

```text
Username: admin
Password: 123
```

Demo users are also available:

```text
manager / 123
employee / 123
```

## Tech Stack

- Frontend: Streamlit
- Backend: FastAPI
- Database: SQLite
- Language: Python

## Project Files

```text
backend.py      FastAPI backend with SQLite database logic
frontend.py     Streamlit frontend dashboard
leaveflow.db    SQLite database file created automatically
```

## How To Run

Install the required packages:

```bash
pip install fastapi uvicorn streamlit pandas requests
```

Start the backend:

```bash
uvicorn backend:app --reload
```

Start the frontend in another terminal:

```bash
streamlit run frontend.py
```

Then open the Streamlit URL shown in the terminal.

## Leave Balance Rules

Default balances for managers and employees:

```text
Earned Leave: 10
Sick Leave: 12
Casual Leave: 6
```

When an employee applies for leave, the balance is reduced immediately. If the manager approves the request, no further balance change happens. If the manager rejects the request, the deducted balance is added back automatically.

## Roles

Admin can manage users, holidays, employee-manager mapping, leave reports, and organization dashboards.

Manager can view team requests, approve or reject leave, inspect reports, and view the holiday calendar.

Employee can apply for leave, view leave history, track balances, and view the holiday calendar.
