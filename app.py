
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

# ---------- Page settings ----------
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
)

DB_PATH = Path(__file__).with_name("expenses.db")

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Education",
    "Health",
    "Entertainment",
    "Other",
]


# ---------- Database functions ----------
def connect_db():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)


def add_expense(amount, category, description, expense_date):
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO expenses
            (amount, category, description, expense_date)
            VALUES (?, ?, ?, ?)
            """,
            (amount, category, description, expense_date.isoformat()),
        )


def load_expenses():
    with connect_db() as conn:
        return pd.read_sql_query(
            """
            SELECT id, amount, category, description, expense_date
            FROM expenses
            ORDER BY expense_date DESC, id DESC
            """,
            conn,
        )


def remove_expense(expense_id):
    with connect_db() as conn:
        conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (int(expense_id),),
        )


initialize_db()


# ---------- Design ----------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}
div[data-testid="stMetric"] {
    background: rgba(128, 128, 128, 0.08);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(128, 128, 128, 0.18);
}
</style>
""", unsafe_allow_html=True)


# ---------- Header ----------
st.title("💰 Personal Expense Tracker")
st.caption("Manage your money. Track your habits. Spend smarter.")

st.divider()


# ---------- Add expense form ----------
with st.sidebar:
    st.header("➕ Add New Expense")

    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=100.0,
            step=10.0,
        )

        category = st.selectbox("Category", CATEGORIES)

        description = st.text_input(
            "Description",
            placeholder="e.g. Lunch, bus ticket",
        )

        expense_date = st.date_input(
            "Expense date",
            value=date.today(),
            max_value=date.today(),
        )

        submitted = st.form_submit_button(
            "Save Expense",
            use_container_width=True,
        )

        if submitted:
            if not description.strip():
                st.error("Please enter a description.")
            else:
                add_expense(
                    amount,
                    category,
                    description.strip(),
                    expense_date,
                )
                st.session_state["notice"] = (
                    f"Expense of ₹{amount:,.2f} saved successfully!"
                )
                st.rerun()

    st.divider()
    st.caption("Your expenses are stored locally on your computer.")


# ---------- Load saved records ----------
expenses = load_expenses()

if st.session_state.get("notice"):
    st.success(st.session_state.pop("notice"))


# ---------- Dashboard ----------
st.subheader("📊 Dashboard")

total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
count = len(expenses)
average = total / count if count else 0.0

col1, col2, col3 = st.columns(3)

col1.metric("Total Expenses", f"₹{total:,.2f}")
col2.metric("Total Transactions", count)
col3.metric("Average Expense", f"₹{average:,.2f}")

st.divider()


# ---------- Charts ----------
st.subheader("📈 Expense Analytics")

if expenses.empty:
    st.info(
        "Your chart will appear here after you save your first expense. "
        "Use the form in the left sidebar to get started."
    )
else:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Spending by Category**")

        category_totals = (
            expenses.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(category_totals)

    with chart_col2:
        st.markdown("**Spending by Date**")

        daily_totals = expenses.copy()
        daily_totals["expense_date"] = pd.to_datetime(
            daily_totals["expense_date"]
        )

        daily_totals = (
            daily_totals.groupby("expense_date")["amount"]
            .sum()
            .sort_index()
        )

        st.line_chart(daily_totals)


st.divider()


# ---------- Expense history ----------
st.subheader("🧾 All Transactions")

if expenses.empty:
    st.write("No expenses recorded yet.")
else:
    display_df = expenses[
        ["expense_date", "description", "category", "amount"]
    ].copy()

    display_df.columns = [
        "Date", "Description", "Category", "Amount (₹)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Export Expenses to CSV",
        data=display_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="my_expenses.csv",
        mime="text/csv",
    )

    st.divider()

    # ---------- Delete expense ----------
    st.subheader("🗑️ Delete a Transaction")

    expense_options = {
        (
            f"#{row.id} | {row.expense_date} | "
            f"{row.description} | ₹{row.amount:,.2f}"
        ): int(row.id)
        for row in expenses.itertuples(index=False)
    }

    with st.form("delete_form"):
        selected = st.selectbox(
            "Choose a transaction",
            list(expense_options.keys()),
        )

        confirm = st.checkbox("I confirm this deletion.")

        delete_clicked = st.form_submit_button("Delete Transaction")

        if delete_clicked:
            if confirm:
                remove_expense(expense_options[selected])
                st.session_state["notice"] = "Transaction deleted."
                st.rerun()
            else:
                st.warning("Please confirm before deleting.")

st.divider()
st.caption("Personal Expense Tracker | Python + Streamlit + SQLite")
