import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


DB_PATH = Path(__file__).with_name("leaveflow.db")

app = FastAPI(title="Role Based Leave Management API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Role = Literal["employee", "manager", "admin"]
LeaveStatus = Literal["pending", "approved", "rejected"]
LeaveType = Literal["earned", "sick", "casual", "unpaid"]
DayMode = Literal["full", "half"]


class LoginRequest(BaseModel):
    username: str
    password: str


class EmployeeCreate(BaseModel):
    username: str
    password: str
    name: str
    email: str
    department: str
    role: Role = "employee"
    manager: str | None = None
    sick_balance: float = 12
    casual_balance: float = 6
    earned_balance: float = 10


class EmployeeUpdate(BaseModel):
    name: str
    email: str
    department: str
    role: Role
    manager: str | None = None
    sick_balance: float = 12
    casual_balance: float = 6
    earned_balance: float = 10
    new_password: str | None = None


class LeaveCreate(BaseModel):
    username: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    day_mode: DayMode = "full"
    reason: str


class LeaveDecision(BaseModel):
    manager_username: str
    status: Literal["approved", "rejected"]
    comments: str = ""


class HolidayCreate(BaseModel):
    name: str
    holiday_date: date


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    return dict(row) if row else None


def execute(query, params=()):
    with db() as conn:
        cur = conn.execute(query, params)
        conn.commit()
        return cur


def fetchone(query, params=()):
    with db() as conn:
        return row_to_dict(conn.execute(query, params).fetchone())


def fetchall(query, params=()):
    with db() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def balance_dict(user):
    return {
        "earned": user["earned_balance"],
        "sick": user["sick_balance"],
        "casual": user["casual_balance"],
        "unpaid": user["unpaid_balance"],
    }


def public_user(user):
    data = dict(user)
    data.pop("password", None)
    data["balances"] = balance_dict(user)
    return data


def employee_row(user):
    return {
        "emp_id": user["emp_id"],
        "username": user["username"],
        "name": user["name"],
        "email": user["email"],
        "department": user["department"],
        "role": user["role"],
        "manager": user["manager"] or "-",
        "earned_leave": user["earned_balance"],
        "sick_leave": user["sick_balance"],
        "casual_leave": user["casual_balance"],
    }


def next_emp_id(role: str) -> str:
    if role == "manager":
        prefix, start = "GENAIM", 1150
    elif role == "employee":
        prefix, start = "GENAIE", 2650
    else:
        prefix, start = "GENAIA", 1000

    existing = fetchall("SELECT emp_id FROM users WHERE emp_id LIKE ?", (f"{prefix}%",))
    numbers = []
    for item in existing:
        suffix = item["emp_id"].replace(prefix, "")
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{prefix}{(max(numbers) + 1) if numbers else start}"


def indian_holidays_2026():
    return [
        ("New Year's Day", "2026-01-01"),
        ("Makar Sankranti", "2026-01-14"),
        ("Republic Day", "2026-01-26"),
        ("Maha Shivaratri", "2026-02-15"),
        ("Holi", "2026-03-04"),
        ("Good Friday", "2026-04-03"),
        ("Eid al-Fitr", "2026-03-20"),
        ("Mahavir Jayanti", "2026-03-31"),
        ("Ambedkar Jayanti", "2026-04-14"),
        ("May Day", "2026-05-01"),
        ("Buddha Purnima", "2026-05-01"),
        ("Eid al-Adha", "2026-05-27"),
        ("Muharram", "2026-06-26"),
        ("Independence Day", "2026-08-15"),
        ("Janmashtami", "2026-09-04"),
        ("Gandhi Jayanti", "2026-10-02"),
        ("Dussehra", "2026-10-20"),
        ("Diwali", "2026-11-08"),
        ("Guru Nanak Jayanti", "2026-11-24"),
        ("Christmas", "2026-12-25"),
    ]


def init_db():
    execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            emp_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT NOT NULL,
            manager TEXT,
            earned_balance REAL NOT NULL DEFAULT 10,
            sick_balance REAL NOT NULL DEFAULT 12,
            casual_balance REAL NOT NULL DEFAULT 6,
            unpaid_balance REAL NOT NULL DEFAULT 999
        )
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS holidays (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            holiday_date TEXT NOT NULL
        )
        """
    )
    holidays_schema = fetchone("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'holidays'")
    if holidays_schema and "UNIQUE" in holidays_schema["sql"].upper():
        execute(
            """
            CREATE TABLE IF NOT EXISTS holidays_new (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                holiday_date TEXT NOT NULL
            )
            """
        )
        execute("INSERT OR IGNORE INTO holidays_new (id, name, holiday_date) SELECT id, name, holiday_date FROM holidays")
        execute("DROP TABLE holidays")
        execute("ALTER TABLE holidays_new RENAME TO holidays")
    execute(
        """
        CREATE TABLE IF NOT EXISTS leave_requests (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            manager TEXT,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            day_mode TEXT NOT NULL DEFAULT 'full',
            days REAL NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            comments TEXT DEFAULT '',
            balance_deducted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    if fetchone("SELECT COUNT(*) AS total FROM users")["total"] == 0:
        default_users = [
            ("admin", "123", "GENAIA1000", "System Admin", "admin@leaveflow.com", "HR", "admin", None, 10, 12, 6, 999),
            ("manager", "123", "GENAIM1150", "Ananya Rao", "ananya.rao@leaveflow.com", "Engineering", "manager", "admin", 10, 12, 6, 999),
            ("employee", "123", "GENAIE2650", "Rahul Mehta", "rahul.mehta@leaveflow.com", "Engineering", "employee", "manager", 10, 12, 6, 999),
        ]
        for item in default_users:
            execute(
                """
                INSERT INTO users (
                    username, password, emp_id, name, email, department, role, manager,
                    earned_balance, sick_balance, casual_balance, unpaid_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                item,
            )

    for name, holiday_date in indian_holidays_2026():
        if not fetchone("SELECT id FROM holidays WHERE name = ? AND holiday_date = ?", (name, holiday_date)):
            try:
                execute(
                    "INSERT INTO holidays (id, name, holiday_date) VALUES (?, ?, ?)",
                    (f"h-{uuid4().hex[:8]}", name, holiday_date),
                )
            except sqlite3.IntegrityError:
                pass


def get_user_or_404(username: str):
    user = fetchone("SELECT * FROM users WHERE username = ?", (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def working_days(start_date: date, end_date: date, day_mode: str) -> float:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")

    holiday_dates = {item["holiday_date"] for item in fetchall("SELECT holiday_date FROM holidays")}
    total = 0
    current = start_date

    while current <= end_date:
        current_text = current.isoformat()
        if current.weekday() < 5 and current_text not in holiday_dates:
            total += 1
        current += timedelta(days=1)

    if day_mode == "half":
        if start_date != end_date:
            raise HTTPException(status_code=400, detail="Half day leave must use the same start and end date")
        return 0.5 if total == 1 else 0
    return float(total)


def serialize_leave(item):
    item["balance_deducted"] = bool(item["balance_deducted"])
    return item


init_db()


@app.get("/")
def health_check():
    return {"status": "online", "message": "Leave Management API is running", "database": str(DB_PATH)}


@app.post("/login")
def login(payload: LoginRequest):
    user = fetchone("SELECT * FROM users WHERE username = ?", (payload.username,))
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return public_user(user)


@app.get("/employees")
def list_employees():
    return [public_user(user) for user in fetchall("SELECT * FROM users ORDER BY role, name")]


@app.get("/employees/table")
def list_employee_table():
    return [employee_row(user) for user in fetchall("SELECT * FROM users ORDER BY role, name")]


@app.post("/employees")
def create_employee(payload: EmployeeCreate):
    if fetchone("SELECT username FROM users WHERE username = ?", (payload.username,)):
        raise HTTPException(status_code=409, detail="Username already exists")
    if payload.manager and not fetchone("SELECT username FROM users WHERE username = ?", (payload.manager,)):
        raise HTTPException(status_code=404, detail="Manager does not exist")

    manager = "admin" if payload.role == "manager" else payload.manager
    if payload.role == "admin":
        manager = None

    emp_id = next_emp_id(payload.role)
    execute(
        """
        INSERT INTO users (
            username, password, emp_id, name, email, department, role, manager,
            earned_balance, sick_balance, casual_balance, unpaid_balance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.username,
            payload.password,
            emp_id,
            payload.name,
            payload.email,
            payload.department,
            payload.role,
            manager,
            payload.earned_balance,
            payload.sick_balance,
            payload.casual_balance,
            999,
        ),
    )
    return public_user(get_user_or_404(payload.username))


@app.patch("/employees/{username}")
def update_employee(username: str, payload: EmployeeUpdate):
    user = get_user_or_404(username)
    if username == "admin" and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Admin role cannot be changed")
    if payload.manager and not fetchone("SELECT username FROM users WHERE username = ?", (payload.manager,)):
        raise HTTPException(status_code=404, detail="Manager does not exist")

    manager = "admin" if payload.role == "manager" else payload.manager
    if payload.role == "admin":
        manager = None
    password = payload.new_password.strip() if payload.new_password and payload.new_password.strip() else user["password"]

    execute(
        """
        UPDATE users
        SET password = ?, name = ?, email = ?, department = ?, role = ?, manager = ?,
            earned_balance = ?, sick_balance = ?, casual_balance = ?
        WHERE username = ?
        """,
        (
            password,
            payload.name,
            payload.email,
            payload.department,
            payload.role,
            manager,
            payload.earned_balance,
            payload.sick_balance,
            payload.casual_balance,
            username,
        ),
    )
    return public_user(get_user_or_404(username))


@app.delete("/employees/{username}")
def delete_employee(username: str):
    user = get_user_or_404(username)
    if username == "admin":
        raise HTTPException(status_code=400, detail="Admin user cannot be deleted")
    if fetchone("SELECT id FROM leave_requests WHERE username = ? AND status = 'pending'", (username,)):
        raise HTTPException(status_code=400, detail="Cannot delete a user with pending leave requests")

    execute("UPDATE users SET manager = NULL WHERE manager = ?", (username,))
    execute("DELETE FROM leave_requests WHERE username = ?", (username,))
    execute("DELETE FROM users WHERE username = ?", (username,))
    return {"deleted": True, "username": user["username"]}


@app.get("/employees/{username}/balances")
def get_balances(username: str):
    return balance_dict(get_user_or_404(username))


@app.post("/leave")
def apply_leave(payload: LeaveCreate):
    user = get_user_or_404(payload.username)
    days = working_days(payload.start_date, payload.end_date, payload.day_mode)
    if days <= 0:
        raise HTTPException(status_code=400, detail="Selected dates contain no working days")

    balance_key = f"{payload.leave_type}_balance"
    balance = user[balance_key] if payload.leave_type != "unpaid" else 999
    if payload.leave_type != "unpaid" and balance < days:
        raise HTTPException(status_code=400, detail="Insufficient leave balance")

    if payload.leave_type != "unpaid":
        execute(f"UPDATE users SET {balance_key} = {balance_key} - ? WHERE username = ?", (days, payload.username))

    request_id = f"L-{uuid4().hex[:6].upper()}"
    execute(
        """
        INSERT INTO leave_requests (
            id, username, employee_name, department, manager, leave_type, start_date,
            end_date, day_mode, days, reason, status, comments, balance_deducted, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            payload.username,
            user["name"],
            user["department"],
            user["manager"],
            payload.leave_type,
            payload.start_date.isoformat(),
            payload.end_date.isoformat(),
            payload.day_mode,
            days,
            payload.reason,
            "pending",
            "",
            1 if payload.leave_type != "unpaid" else 0,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return serialize_leave(fetchone("SELECT * FROM leave_requests WHERE id = ?", (request_id,)))


@app.get("/leave")
def list_leave_requests(username: str | None = None, role: Role | None = None):
    if not username or not role or role == "admin":
        return [serialize_leave(item) for item in fetchall("SELECT * FROM leave_requests ORDER BY created_at DESC")]
    if role == "manager":
        return [
            serialize_leave(item)
            for item in fetchall("SELECT * FROM leave_requests WHERE manager = ? ORDER BY created_at DESC", (username,))
        ]
    return [
        serialize_leave(item)
        for item in fetchall("SELECT * FROM leave_requests WHERE username = ? ORDER BY created_at DESC", (username,))
    ]


@app.patch("/leave/{request_id}/decision")
def decide_leave(request_id: str, payload: LeaveDecision):
    manager = get_user_or_404(payload.manager_username)
    if manager["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Only managers or admins can approve leave")

    request = fetchone("SELECT * FROM leave_requests WHERE id = ?", (request_id,))
    if not request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if manager["role"] == "manager" and request["manager"] != payload.manager_username:
        raise HTTPException(status_code=403, detail="Managers can decide only their team requests")
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request has already been decided")

    balance_deducted = request["balance_deducted"]
    if payload.status == "rejected" and balance_deducted and request["leave_type"] != "unpaid":
        balance_key = f"{request['leave_type']}_balance"
        execute("UPDATE users SET " + balance_key + " = " + balance_key + " + ? WHERE username = ?", (request["days"], request["username"]))
        balance_deducted = 0

    execute(
        "UPDATE leave_requests SET status = ?, comments = ?, balance_deducted = ? WHERE id = ?",
        (payload.status, payload.comments, balance_deducted, request_id),
    )
    return serialize_leave(fetchone("SELECT * FROM leave_requests WHERE id = ?", (request_id,)))


@app.get("/holidays")
def list_holidays():
    return fetchall("SELECT * FROM holidays ORDER BY holiday_date")


@app.post("/holidays")
def create_holiday(payload: HolidayCreate):
    holiday_id = f"h-{uuid4().hex[:8]}"
    try:
        execute(
            "INSERT INTO holidays (id, name, holiday_date) VALUES (?, ?, ?)",
            (holiday_id, payload.name, payload.holiday_date.isoformat()),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Holiday already exists for this date")
    return fetchone("SELECT * FROM holidays WHERE id = ?", (holiday_id,))


@app.get("/reports/summary")
def report_summary():
    requests = fetchall("SELECT * FROM leave_requests")
    total = len(requests)
    approved = len([item for item in requests if item["status"] == "approved"])
    rejected = len([item for item in requests if item["status"] == "rejected"])
    pending = len([item for item in requests if item["status"] == "pending"])
    approved_days = sum(item["days"] for item in requests if item["status"] == "approved")

    by_type = {}
    by_status = {}
    by_manager = {}
    for item in requests:
        by_type[item["leave_type"]] = by_type.get(item["leave_type"], 0) + item["days"]
        by_status[item["status"]] = by_status.get(item["status"], 0) + item["days"]
        by_manager[item["manager"] or "-"] = by_manager.get(item["manager"] or "-", 0) + item["days"]

    return {
        "total_requests": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "approved_days": approved_days,
        "leave_days_by_type": by_type,
        "leave_days_by_status": by_status,
        "leave_days_by_manager": by_manager,
        "audit_logs": [
            f"{item['id']} - {item['employee_name']} requested {item['days']} {item['leave_type']} day(s): {item['status']}"
            for item in requests
        ],
    }


@app.get("/reports/organization")
def organization_report():
    all_users = fetchall("SELECT * FROM users ORDER BY role, name")
    employee_count = len([user for user in all_users if user["role"] == "employee"])
    manager_count = len([user for user in all_users if user["role"] == "manager"])
    admin_count = len([user for user in all_users if user["role"] == "admin"])
    mapping = {}

    for user in all_users:
        if user["role"] == "employee" and user["manager"]:
            mapping.setdefault(user["manager"], []).append(employee_row(user))

    return {
        "employees": employee_count,
        "managers": manager_count,
        "admins": admin_count,
        "total_strength": len(all_users),
        "manager_mapping": mapping,
    }
