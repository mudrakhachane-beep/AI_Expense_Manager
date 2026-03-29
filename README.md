Overview
AI Expense Manager is a full-stack Streamlit application that streamlines corporate expense tracking and approval through a multi-role workflow. Employees submit expenses via natural language or a manual form, managers review and approve them, and admins oversee the entire organisation — all augmented by Google Gemini for smart categorisation, NLP parsing, and AI-generated financial insights.

Features
🔐 Role-Based Authentication
Three distinct dashboards — Admin, Manager, and Employee — each with scoped permissions and a dedicated UI tailored to their responsibilities.
✅ Multi-Level Expense Approval Workflow
Expenses move through a structured pipeline: Pending → Approved / Rejected. Managers review only their direct reports' submissions; Admins can override any record organisation-wide.
🗣️ Natural Language Expense Submission
Employees can describe expenses in plain English — "spent 850 on a team lunch yesterday" — and the app automatically extracts the amount, category, description, and date using Gemini.
🤖 AI-Powered Categorisation
Every expense description is classified into one of seven categories (Food, Travel, Accommodation, Office Supplies, Medical, Entertainment, Other) by Gemini, with a one-click suggestion in the submission form.
📊 Spending Analytics & Charts

Manager view — donut chart of category-wise team spending with status and category filters.
Admin view — bar chart of employee-wise total expenditure across the organisation.

💡 AI Financial Insights
Admins can trigger Gemini to analyse the full expense dataset and receive three concrete, data-driven saving recommendations tailored to actual spending patterns.
