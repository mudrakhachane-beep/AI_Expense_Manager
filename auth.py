import pandas as pd
import os

USERS_CSV_PATH = "data/user.csv"


def load_users() -> pd.DataFrame:
    """Load users from the CSV file and return as a DataFrame."""
    if not os.path.exists(USERS_CSV_PATH):
        raise FileNotFoundError(f"Users file not found at: {USERS_CSV_PATH}")
    df = pd.read_csv(USERS_CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()
    return df


def login(username: str, password: str) -> tuple:
    """
    Validate credentials against the users CSV.

    Returns:
        (True, role, manager_username) on success
        (False, None, None) on failure
    """
    try:
        df = load_users()
    except FileNotFoundError:
        return False, None, None

    match = df[
        (df["username"].astype(str).str.strip() == username.strip()) &
        (df["password"].astype(str).str.strip() == password.strip())
    ]

    if match.empty:
        return False, None, None

    user = match.iloc[0]
    role = user.get("role", None)
    manager_username = user.get("manager_username", None)

    # Normalize NaN to None
    role = None if pd.isna(role) else str(role).strip()
    manager_username = None if pd.isna(manager_username) else str(manager_username).strip()

    return True, role, manager_username


def get_all_employees(manager_username: str) -> list:
    """
    Return a list of employee usernames that report to the given manager.

    Args:
        manager_username: The username of the manager.

    Returns:
        List of employee usernames under that manager.
    """
    try:
        df = load_users()
    except FileNotFoundError:
        return []

    if "manager_username" not in df.columns:
        return []

    employees = df[
        df["manager_username"].astype(str).str.strip() == manager_username.strip()
    ]

    return employees["username"].tolist()


def create_user(
    username: str,
    password: str,
    role: str,
    manager_username: str,
    company: str
) -> bool:
    """
    Append a new user to the users CSV file.

    Returns:
        True if the user was created successfully, False otherwise.
    """
    try:
        df = load_users()
    except FileNotFoundError:
        return False

    # Check for duplicate username
    if username.strip() in df["username"].astype(str).str.strip().values:
        raise ValueError(f"Username '{username}' already exists.")

    new_user = pd.DataFrame([{
        "username": username.strip(),
        "password": password.strip(),
        "role": role.strip(),
        "manager_username": manager_username.strip() if manager_username else "",
        "company": company.strip()
    }])

    updated_df = pd.concat([df, new_user], ignore_index=True)
    os.makedirs(os.path.dirname(USERS_CSV_PATH), exist_ok=True)
    updated_df.to_csv(USERS_CSV_PATH, index=False)

    return True