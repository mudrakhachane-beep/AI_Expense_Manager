import os
import json
import re
from datetime import datetime, timedelta

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found. Please set it in your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

_MODEL_NAME = "gemini-2.5-flash"
_model = genai.GenerativeModel(_MODEL_NAME)

VALID_CATEGORIES = [
    "Food",
    "Travel",
    "Accommodation",
    "Office Supplies",
    "Medical",
    "Entertainment",
    "Other",
]


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the stripped text response."""
    response = _model.generate_content(prompt)
    return response.text.strip()


def categorize_expense(description: str) -> str:
    """
    Use Gemini to classify an expense description into a predefined category.

    Args:
        description: Free-text expense description (e.g. 'team lunch at restaurant').

    Returns:
        One category string from VALID_CATEGORIES. Falls back to 'Other' if
        Gemini returns an unrecognised value.
    """
    categories_list = ", ".join(VALID_CATEGORIES)

    prompt = f"""You are an expense classification assistant.

Your task is to classify the following expense description into exactly one of these categories:
{categories_list}

Rules:
- Return ONLY the category name, nothing else.
- Do not add punctuation, explanation, or extra words.
- If the description does not clearly match any category, return: Other

Expense description: "{description}"

Category:"""

    result = _call_gemini(prompt)

    # Validate the returned category
    for category in VALID_CATEGORIES:
        if category.lower() == result.lower():
            return category

    return "Other"


def get_insights(expenses_df) -> str:
    """
    Analyse an expenses DataFrame and return 3 bullet-point saving suggestions.

    Args:
        expenses_df: A pandas DataFrame with at least these columns:
                     category, amount, currency, date.

    Returns:
        A string with exactly 3 bullet-point suggestions.
    """
    if expenses_df.empty:
        return "• No expense data available to generate insights."

    # Build a concise summary to stay within token limits
    total = expenses_df["amount"].sum()
    currency = expenses_df["currency"].iloc[0] if "currency" in expenses_df.columns else "USD"

    category_summary = (
        expenses_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    category_lines = "\n".join(
        f"  - {row['category']}: {currency} {row['amount']:.2f}"
        for _, row in category_summary.iterrows()
    )

    date_range = ""
    if "date" in expenses_df.columns:
        dates = expenses_df["date"].dropna().astype(str)
        if not dates.empty:
            date_range = f"Period: {dates.min()} to {dates.max()}\n"

    summary_text = (
        f"{date_range}"
        f"Total spent: {currency} {total:.2f}\n"
        f"Number of expenses: {len(expenses_df)}\n"
        f"Breakdown by category:\n{category_lines}"
    )

    prompt = f"""You are a personal finance advisor reviewing an employee's expense report.

Based on the following expense summary, provide exactly 3 concise, actionable saving suggestions.

Expense Summary:
{summary_text}

Instructions:
- Return exactly 3 bullet points.
- Start each bullet point with "• ".
- Each suggestion must be specific to the data above, not generic advice.
- Keep each point to 1–2 sentences.
- Do not include any heading, preamble, or closing remarks.

Suggestions:"""

    return _call_gemini(prompt)


def parse_expense_nlp(text: str) -> dict:
    """
    Parse a natural-language expense description into structured fields.

    Args:
        text: Natural language input, e.g. "spent 500 on food yesterday".

    Returns:
        A dict with keys: amount (float), category (str), description (str), date (str YYYY-MM-DD).
        Returns a dict with an 'error' key if parsing fails.
    """
    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    categories_list = ", ".join(VALID_CATEGORIES)

    prompt = f"""You are an expense parsing assistant.

Today's date is: {today_str}

Parse the following natural language expense entry and extract structured data.

Input: "{text}"

Rules:
1. Return ONLY a valid JSON object — no markdown, no code fences, no explanation.
2. The JSON must have exactly these keys:
   - "amount": a number (float or int), no currency symbols
   - "category": one of [{categories_list}]
   - "description": a short cleaned-up description of the expense
   - "date": an absolute date in YYYY-MM-DD format
3. Resolve relative dates using today's date ({today_str}):
   - "today"     → {today_str}
   - "yesterday" → {yesterday_str}
   - "X days ago" → calculate from {today_str}
   - If no date is mentioned, default to {today_str}
4. If amount cannot be determined, use 0.0
5. If category cannot be determined, use "Other"

JSON output:"""

    raw = _call_gemini(prompt)

    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to extract JSON object substring as a fallback
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                return {"error": "Failed to parse Gemini response as JSON.", "raw": raw}
        else:
            return {"error": "No JSON object found in Gemini response.", "raw": raw}

    # Coerce and validate fields
    result = {
        "amount":      float(parsed.get("amount", 0.0)),
        "category":    parsed.get("category", "Other"),
        "description": str(parsed.get("description", text)).strip(),
        "date":        str(parsed.get("date", today_str)).strip(),
    }

    # Validate category
    if result["category"] not in VALID_CATEGORIES:
        result["category"] = "Other"

    # Validate date format
    try:
        datetime.strptime(result["date"], "%Y-%m-%d")
    except ValueError:
        result["date"] = today_str

    return result