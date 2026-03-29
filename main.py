import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

from auth import login, create_user, get_all_employees, load_users
from utils import (
    save_expense,
    get_expenses_by_user,
    get_expenses_by_manager,
    get_all_expenses,
    update_status,
)
from AI_module import categorize_expense, get_insights, parse_expense_nlp



df = pd.read_csv("data/user.csv")
print(df)
print(df.columns.tolist())


# ─────────────────────────────────────────────
# PAGE CONFIG & GLOBAL STYLES
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ExpenseIQ",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Background ── */
    .stApp {
        background: #374151;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0F1117;
        border-right: 1px solid #1E2130;
    }
    [data-testid="stSidebar"] * {
        color: #C9CDD8 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.88rem;
        letter-spacing: 0.02em;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #E8EAF0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    /* ── Buttons ── */
    .stButton > button {
        background: #1A56DB;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.45rem 1.1rem;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #1444B8;
    }

    /* Approve / Reject overrides via key classes set via container */
    .approve-btn button { background: #0E9F6E !important; }
    .approve-btn button:hover { background: #057A55 !important; }
    .reject-btn button { background: #E02424 !important; }
    .reject-btn button:hover { background: #C81E1E !important; }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tab"] {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.88rem;
        font-weight: 500;
        color: #6B7280;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #1A56DB !important;
        border-bottom: 2px solid #1A56DB;
    }

    /* ── Inputs ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb] {
        border-radius: 8px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    /* ── Page headings ── */
    .page-header {
        padding: 0.5rem 0 1.5rem 0;
        border-bottom: 1px solid #E8EAF0;
        margin-bottom: 1.5rem;
    }
    .page-header h1 {
        font-size: 1.55rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
    }
    .page-header p {
        font-size: 0.85rem;
        color: #6B7280;
        margin: 0.2rem 0 0 0;
    }

    /* ── Status badges ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 500;
        font-family: 'DM Mono', monospace;
    }
    .badge-pending  { background: #FEF3C7; color: #92400E; }
    .badge-approved { background: #D1FAE5; color: #065F46; }
    .badge-rejected { background: #FEE2E2; color: #991B1B; }

    /* ── Card shell ── */
    .card {
        background: #ffffff;
        border: 1px solid #E8EAF0;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* ── Login wrapper ── */
    .login-card {
        max-width: 420px;
        margin: 6vh auto;
        background: #ffffff;
        border: 1px solid #E8EAF0;
        border-radius: 18px;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    }
    .login-logo {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1A56DB;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    .login-sub {
        font-size: 0.83rem;
        color: #9CA3AF;
        margin-bottom: 1.8rem;
    }

    /* ── Insight block ── */
    .insight-block {
        background: #EFF6FF;
        border-left: 4px solid #1A56DB;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        font-size: 0.9rem;
        color: #1E3A5F;
        line-height: 1.6;
    }

    /* hide streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# SESSION STATE HELPERS
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username": None,
        "role": None,
        "manager_username": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def do_logout():
    for k in ["logged_in", "username", "role", "manager_username"]:
        st.session_state[k] = None
    st.session_state["logged_in"] = False
    st.rerun()


# ─────────────────────────────────────────────
# SHARED UTILITIES
# ─────────────────────────────────────────────
CATEGORIES = [
    "Food", "Travel", "Accommodation",
    "Office Supplies", "Medical", "Entertainment", "Other",
]
CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED"]
STATUS_COLORS = {"Pending": "#F59E0B", "Approved": "#10B981", "Rejected": "#EF4444"}


def styled_status(status: str) -> str:
    cls = {"Pending": "badge-pending", "Approved": "badge-approved", "Rejected": "badge-rejected"}.get(status, "")
    return f'<span class="badge {cls}">{status}</span>'


def render_expense_table(df: pd.DataFrame, show_user: bool = False):
    """Render a clean HTML expense table."""
    if df.empty:
        st.info("No expenses found.")
        return

    cols_to_show = []
    if show_user:
        cols_to_show.append("username")
    cols_to_show += ["expense_id", "date", "category", "amount", "currency",
                     "description", "status", "approver_comments"]
    cols_present = [c for c in cols_to_show if c in df.columns]
    display_df = df[cols_present].copy()

    if "status" in display_df.columns:
        display_df["status"] = display_df["status"].apply(styled_status)

    if "expense_id" in display_df.columns:
        display_df["expense_id"] = display_df["expense_id"].astype(str).str[:8] + "…"

    st.write(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def page_login():
    st.markdown(
        """
        <div class="login-card">
            <div class="login-logo">💼 ExpenseIQ</div>
            <div class="login-sub">AI-powered expense management</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centre the form
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        with st.container(border=True):
            st.markdown("#### Sign in to your account")
            username = st.text_input("Username", placeholder="e.g. john.doe")
            password = st.text_input("Password", type="password", placeholder="••••••••")

            if st.button("Sign In", use_container_width=True):
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    success, role, manager_username = login(username, password)
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = role
                        st.session_state["manager_username"] = manager_username
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")


# ─────────────────────────────────────────────
# EMPLOYEE DASHBOARD
# ─────────────────────────────────────────────
def page_employee():
    username = st.session_state["username"]

    st.markdown(
        f"""<div class="page-header">
            <h1>Employee Dashboard</h1>
            <p>Welcome back, <strong>{username}</strong></p>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_submit, tab_history = st.tabs(["➕  Submit Expense", "📋  My Expenses"])

    # ── TAB 1: SUBMIT ────────────────────────────────────────────
    with tab_submit:
        st.markdown("##### 🤖 Auto-fill with Natural Language")
        nlp_col, btn_col = st.columns([5, 1])
        with nlp_col:
            nlp_text = st.text_input(
                "Describe your expense",
                placeholder='e.g. "Spent 850 on a team dinner yesterday"',
                label_visibility="collapsed",
            )
        with btn_col:
            parse_clicked = st.button("Parse", use_container_width=True)

        # NLP parsing state
        if "nlp_prefill" not in st.session_state:
            st.session_state["nlp_prefill"] = {}

        if parse_clicked and nlp_text.strip():
            with st.spinner("Analysing with AI…"):
                parsed = parse_expense_nlp(nlp_text)
            if "error" not in parsed:
                st.session_state["nlp_prefill"] = parsed
                st.success("Form auto-filled from your description.")
            else:
                st.warning(f"Could not parse: {parsed.get('error')}")

        prefill = st.session_state.get("nlp_prefill", {})

        st.markdown("##### Manual / Confirmed Details")

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                amount = st.number_input(
                    "Amount",
                    min_value=0.01,
                    value=float(prefill.get("amount", 0.01)),
                    step=0.01,
                    format="%.2f",
                )
                default_date = prefill.get("date", str(date.today()))
                try:
                    parsed_date = datetime.strptime(default_date, "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = date.today()
                expense_date = st.date_input("Date", value=parsed_date)

            with c2:
                currency = st.selectbox("Currency", CURRENCIES)
                prefill_cat = prefill.get("category", CATEGORIES[0])
                cat_index = CATEGORIES.index(prefill_cat) if prefill_cat in CATEGORIES else 0
                category = st.selectbox("Category", CATEGORIES, index=cat_index)

            description = st.text_area(
                "Description",
                value=prefill.get("description", ""),
                placeholder="Brief description of the expense…",
                height=90,
            )

            ai_col, submit_col = st.columns([1, 1])
            with ai_col:
                if st.button("🤖 AI Suggest Category", use_container_width=True):
                    if description.strip():
                        with st.spinner("Categorising…"):
                            suggested = categorize_expense(description)
                        st.info(f"AI suggests: **{suggested}**")
                    else:
                        st.warning("Enter a description first.")
            with submit_col:
                if st.button("✅ Submit Expense", use_container_width=True):
                    if not description.strip():
                        st.warning("Please add a description.")
                    else:
                        expense_id = save_expense(
                            username=username,
                            amount=amount,
                            currency=currency,
                            category=category,
                            description=description,
                            date=str(expense_date),
                        )
                        st.success(f"Expense submitted! ID: `{expense_id[:8]}…`")
                        st.session_state["nlp_prefill"] = {}
                        st.rerun()

    # ── TAB 2: HISTORY ──────────────────────────────────────────
    with tab_history:
        df = get_expenses_by_user(username)
        if df.empty:
            st.info("You have no expenses yet. Submit your first expense above.")
        else:
            total = df["amount"].sum()
            pending_count = (df["status"] == "Pending").sum()
            approved_count = (df["status"] == "Approved").sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Submitted", f"₹ {total:,.2f}")
            m2.metric("Pending", int(pending_count))
            m3.metric("Approved", int(approved_count))

            st.markdown("---")
            render_expense_table(df)


# ─────────────────────────────────────────────
# MANAGER DASHBOARD
# ─────────────────────────────────────────────
def page_manager():
    username = st.session_state["username"]

    st.markdown(
        f"""<div class="page-header">
            <h1>Manager Dashboard</h1>
            <p>Logged in as <strong>{username}</strong></p>
        </div>""",
        unsafe_allow_html=True,
    )

    try:
        users_df = load_users()
    except FileNotFoundError:
        st.error("Users file not found.")
        return

    tab_approvals, tab_overview = st.tabs(["⏳  Pending Approvals", "👥  Team Overview"])

    # ── TAB 1: APPROVALS ────────────────────────────────────────
    with tab_approvals:
        pending_df = get_expenses_by_manager(username, users_df)

        if pending_df.empty:
            st.success("🎉 No pending approvals — all caught up!")
        else:
            st.markdown(f"**{len(pending_df)} expense(s) awaiting your review**")

            for _, row in pending_df.iterrows():
                with st.container(border=True):
                    h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
                    h1.markdown(f"**{row.get('username', '—')}**  ·  {row.get('description', '')}")
                    h2.markdown(f"`{row.get('category', '—')}`")
                    h3.markdown(f"**{row.get('currency', '')} {row.get('amount', 0):,.2f}**")
                    h4.markdown(f"{row.get('date', '—')}")

                    short_id = str(row["expense_id"])[:8]
                    comment_key = f"comment_{row['expense_id']}"
                    comment = st.text_input(
                        "Comment (optional)",
                        key=comment_key,
                        placeholder="Add a note…",
                        label_visibility="collapsed",
                    )

                    a_col, r_col, _ = st.columns([1, 1, 4])
                    with a_col:
                        if st.button(f"✅ Approve", key=f"approve_{row['expense_id']}"):
                            update_status(row["expense_id"], "Approved", comment)
                            st.success(f"Approved {short_id}…")
                            st.rerun()
                    with r_col:
                        if st.button(f"❌ Reject", key=f"reject_{row['expense_id']}"):
                            update_status(row["expense_id"], "Rejected", comment)
                            st.error(f"Rejected {short_id}…")
                            st.rerun()

    # ── TAB 2: TEAM OVERVIEW ────────────────────────────────────
    with tab_overview:
        employees = get_all_employees(username)
        if not employees:
            st.info("No employees found under your account.")
            return

        all_expenses = get_all_expenses()
        if all_expenses.empty:
            st.info("No team expenses yet.")
            return

        team_df = all_expenses[all_expenses["username"].isin(employees)]

        if team_df.empty:
            st.info("No team expenses found.")
            return

        f1, f2 = st.columns(2)
        status_filter = f1.multiselect(
            "Filter by Status",
            ["Pending", "Approved", "Rejected"],
            default=["Pending", "Approved", "Rejected"],
        )
        cat_filter = f2.multiselect(
            "Filter by Category",
            CATEGORIES,
            default=CATEGORIES,
        )

        filtered = team_df[
            team_df["status"].isin(status_filter) &
            team_df["category"].isin(cat_filter)
        ]

        render_expense_table(filtered, show_user=True)

        if not filtered.empty and "category" in filtered.columns:
            st.markdown("---")
            cat_spend = (
                filtered.groupby("category")["amount"]
                .sum()
                .reset_index()
                .rename(columns={"amount": "Total"})
            )
            fig = px.pie(
                cat_spend,
                names="category",
                values="Total",
                title="Category-wise Team Spending",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig.update_layout(
                font_family="DM Sans",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────
def page_admin():
    username = st.session_state["username"]

    st.markdown(
        f"""<div class="page-header">
            <h1>Admin Dashboard</h1>
            <p>Logged in as <strong>{username}</strong> · Full access</p>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_expenses, tab_users, tab_insights = st.tabs([
        "💳  All Expenses",
        "👤  User Management",
        "🤖  AI Insights",
    ])

    # ── TAB 1: ALL EXPENSES ─────────────────────────────────────
    with tab_expenses:
        all_df = get_all_expenses()

        if all_df.empty:
            st.info("No expenses in the system yet.")
        else:
            t1, t2, t3 = st.columns(3)
            t1.metric("Total Expenses", len(all_df))
            t2.metric("Total Value", f"₹ {all_df['amount'].sum():,.2f}")
            t3.metric(
                "Pending",
                int((all_df["status"] == "Pending").sum()),
            )

            st.markdown("---")
            st.markdown("##### Override Status")
            with st.expander("Update an expense status"):
                eid = st.text_input("Expense ID (full)")
                new_status = st.selectbox("New Status", ["Approved", "Rejected"])
                admin_comment = st.text_input("Admin Comment")
                if st.button("Update Status"):
                    if eid.strip():
                        ok = update_status(eid.strip(), new_status, admin_comment)
                        if ok:
                            st.success("Status updated.")
                            st.rerun()
                        else:
                            st.error("Expense ID not found.")
                    else:
                        st.warning("Enter an expense ID.")

            st.markdown("##### All Expense Records")
            render_expense_table(all_df, show_user=True)

            if "username" in all_df.columns:
                st.markdown("---")
                dept_spend = (
                    all_df.groupby("username")["amount"]
                    .sum()
                    .reset_index()
                    .sort_values("amount", ascending=False)
                    .rename(columns={"amount": "Total Spent", "username": "Employee"})
                )
                fig = px.bar(
                    dept_spend,
                    x="Employee",
                    y="Total Spent",
                    title="Employee-wise Total Spending",
                    color="Total Spent",
                    color_continuous_scale="Blues",
                )
                fig.update_layout(
                    font_family="DM Sans",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2: USER MANAGEMENT ──────────────────────────────────
    with tab_users:
        try:
            users_df = load_users()
            st.markdown("##### All Users")
            st.dataframe(users_df, use_container_width=True)
        except FileNotFoundError:
            st.warning("No users file found.")
            users_df = pd.DataFrame()

        st.markdown("---")
        st.markdown("##### Create New User")

        with st.container(border=True):
            u1, u2 = st.columns(2)
            new_username = u1.text_input("Username", key="new_uname")
            new_password = u2.text_input("Password", type="password", key="new_pass")

            u3, u4 = st.columns(2)
            new_role = u3.selectbox("Role", ["Employee", "Manager"], key="new_role")
            new_company = u4.text_input("Company", key="new_company")

            manager_options = ["(none)"]
            if not users_df.empty and "username" in users_df.columns:
                managers = users_df[
                    users_df.get("role", pd.Series()).astype(str).str.strip() == "Manager"
                ]["username"].tolist()
                manager_options += managers

            new_manager = st.selectbox("Assign Manager", manager_options, key="new_mgr")

            if st.button("➕ Create User", use_container_width=True):
                if not new_username.strip() or not new_password.strip():
                    st.warning("Username and password are required.")
                else:
                    try:
                        mgr_val = "" if new_manager == "(none)" else new_manager
                        create_user(
                            username=new_username.strip(),
                            password=new_password.strip(),
                            role=new_role,
                            manager_username=mgr_val,
                            company=new_company.strip(),
                        )
                        st.success(f"User **{new_username}** created as {new_role}.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    # ── TAB 3: AI INSIGHTS ──────────────────────────────────────
    with tab_insights:
        st.markdown("##### 🤖 AI-Powered Saving Suggestions")
        st.markdown(
            "Click below to have the AI analyse all expenses and generate tailored saving recommendations.",
        )

        if st.button("✨ Generate Insights", use_container_width=False):
            all_df = get_all_expenses()
            if all_df.empty:
                st.warning("No expense data available to analyse.")
            else:
                with st.spinner("Analysing expenses with Gemini…"):
                    insights_text = get_insights(all_df)

                st.markdown("---")
                bullets = [
                    line.strip()
                    for line in insights_text.splitlines()
                    if line.strip().startswith("•")
                ]

                if bullets:
                    for bullet in bullets:
                        st.markdown(
                            f'<div class="insight-block">{bullet}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    # Fallback: render raw text
                    st.markdown(
                        f'<div class="insight-block">{insights_text}</div>',
                        unsafe_allow_html=True,
                    )


# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 1rem 0 1.5rem 0;">
                <span style="font-size:1.4rem;font-weight:700;color:#ffffff;letter-spacing:-0.03em;">
                    💼 ExpenseIQ
                </span><br>
                <span style="font-size:0.75rem;color:#6B7280;">AI Expense Management</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        role = st.session_state.get("role", "")
        uname = st.session_state.get("username", "")

        st.markdown(
            f"""
            <div style="background:#1E2130;border-radius:10px;padding:0.7rem 1rem;margin-bottom:1.2rem;">
                <div style="font-size:0.78rem;color:#9CA3AF;">Signed in as</div>
                <div style="font-size:0.92rem;font-weight:600;color:#F9FAFB;">{uname}</div>
                <div style="font-size:0.75rem;color:#6B7280;margin-top:2px;">{role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("🚪  Sign Out", use_container_width=True):
            do_logout()


# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main():
    init_session()

    if not st.session_state["logged_in"]:
        page_login()
        return

    render_sidebar()

    role = st.session_state.get("role", "")

    if role == "Employee":
        page_employee()
    elif role == "Manager":
        page_manager()
    elif role == "Admin":
        page_admin()
    else:
        st.error(f"Unrecognised role: '{role}'. Please contact your administrator.")


if __name__ == "__main__":
    main()