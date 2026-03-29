import pandas as pd
import os
import uuid
from datetime import datetime

EXPENSES_CSV_PATH = "data/expenses.csv"

COLUMNS = [
    "expense_id",
    "username",
    "amount",
    "currency",
    "category",
    "description",
    "date",
    "status",
    "approver_comments",
]


def _load_or_create_expenses() -> pd.DataFrame:
    """Load expenses CSV or create an empty one if it doesn't exist."""
    if os.path.exists(EXPENSES_CSV_PATH):
        df = pd.read_csv(EXPENSES_CSV_PATH)
        # Ensure all expected columns are present
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[COLUMNS]

    os.makedirs(os.path.dirname(EXPENSES_CSV_PATH), exist_ok=True)
    empty_df = pd.DataFrame(columns=COLUMNS)
    empty_df.to_csv(EXPENSES_CSV_PATH, index=False)
    return empty_df


def _save_df(df: pd.DataFrame) -> None:
    """Persist a DataFrame back to the expenses CSV."""
    os.makedirs(os.path.dirname(EXPENSES_CSV_PATH), exist_ok=True)
    df.to_csv(EXPENSES_CSV_PATH, index=False)


def save_expense(
    username: str,
    amount: float,
    currency: str,
    category: str,
    description: str,
    date: str,
) -> str:
    """
    Append a new expense record to the CSV.

    Args:
        username:    The submitting user's username.
        amount:      Expense amount.
        currency:    Currency code (e.g. 'USD', 'INR').
        category:    Expense category (e.g. 'Travel', 'Food').
        description: Free-text description.
        date:        Date string (e.g. 'YYYY-MM-DD').

    Returns:
        The generated expense_id string.
    """
    expense_id = str(uuid.uuid4())

    new_row = pd.DataFrame([{
        "expense_id":        expense_id,
        "username":          str(username).strip(),
        "amount":            float(amount),
        "currency":          str(currency).strip(),
        "category":          str(category).strip(),
        "description":       str(description).strip(),
        "date":              str(date).strip(),
        "status":            "Pending",
        "approver_comments": "",
    }])

    df = _load_or_create_expenses()
    df = pd.concat([df, new_row], ignore_index=True)
    _save_df(df)

    return expense_id


def get_expenses_by_user(username: str) -> pd.DataFrame:
    """
    Return all expenses submitted by a specific user.

    Args:
        username: The username to filter by.

    Returns:
        DataFrame of that user's expenses.
    """
    df = _load_or_create_expenses()
    if df.empty:
        return df

    return df[df["username"].astype(str).str.strip() == username.strip()].reset_index(drop=True)


def get_expenses_by_manager(manager_username: str, users_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return all Pending expenses belonging to employees under a given manager.

    Args:
        manager_username: The manager's username.
        users_df:         Full users DataFrame (must contain 'username' and
                          'manager_username' columns).

    Returns:
        DataFrame of pending expenses for those employees.
    """
    users_df = users_df.copy()
    users_df.columns = users_df.columns.str.strip().str.lower()

    if "manager_username" not in users_df.columns:
        return pd.DataFrame(columns=COLUMNS)

    direct_reports = users_df[
        users_df["manager_username"].astype(str).str.strip() == manager_username.strip()
    ]["username"].astype(str).str.strip().tolist()

    if not direct_reports:
        return pd.DataFrame(columns=COLUMNS)

    df = _load_or_create_expenses()
    if df.empty:
        return df

    pending = df[
        (df["username"].astype(str).str.strip().isin(direct_reports)) &
        (df["status"].astype(str).str.strip() == "Pending")
    ].reset_index(drop=True)

    return pending


def get_all_expenses() -> pd.DataFrame:
    """
    Return the full expenses DataFrame (intended for Admin use).

    Returns:
        Complete expenses DataFrame.
    """
    return _load_or_create_expenses()


def update_status(expense_id: str, status: str, comments: str) -> bool:
    """
    Update the status and approver comments for a given expense.

    Args:
        expense_id: The unique ID of the expense to update.
        status:     New status value (e.g. 'Approved', 'Rejected').
        comments:   Approver's comments.

    Returns:
        True if the record was found and updated, False if not found.
    """
    df = _load_or_create_expenses()

    mask = df["expense_id"].astype(str).str.strip() == expense_id.strip()

    if not mask.any():
        return False

    df.loc[mask, "status"]            = str(status).strip()
    df.loc[mask, "approver_comments"] = str(comments).strip()

    _save_df(df)
    return True