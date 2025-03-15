'''Testing

# 1 Trial'''

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# **🔹 Set Page Config (Must be first command)**
st.set_page_config(layout="wide")  # Always starts in wide mode

# **🔹 Load Data**
file_path = r"Homesick Budget Tracker.xlsx"
xls = pd.ExcelFile(file_path)

df_expenses = pd.read_excel(xls, "Total Spend")
df_artists = pd.read_excel(xls, "Artist Tracker")

# **🔹 Clean Column Names**
df_expenses.columns = df_expenses.columns.str.strip()
df_artists.columns = df_artists.columns.str.strip()

# **🔹 Convert Date Columns**
df_expenses["Date"] = pd.to_datetime(df_expenses["Date"], errors='coerce')
df_artists["Advance Payment Date"] = pd.to_datetime(df_artists["Advance Payment Date"], errors='coerce')
df_artists["Remaining Forecast Payment Date"] = pd.to_datetime(df_artists["Remaining Forecast Payment Date"], errors='coerce')

# **🔹 Format Dates**
date_format = "%d-%b-%Y"
df_expenses["Date"] = df_expenses["Date"].dt.strftime(date_format)
df_artists["Advance Payment Date"] = df_artists["Advance Payment Date"].dt.strftime(date_format)
df_artists["Remaining Forecast Payment Date"] = df_artists["Remaining Forecast Payment Date"].dt.strftime(date_format)

# **🔹 Extract Month-Year**
df_expenses["Month"] = pd.to_datetime(df_expenses["Date"]).dt.strftime("%B %Y")
df_artists["Month"] = pd.to_datetime(df_artists["Advance Payment Date"], errors='coerce').dt.strftime("%B %Y")
df_artists["Month"].fillna(pd.to_datetime(df_artists["Remaining Forecast Payment Date"], errors='coerce').dt.strftime("%B %Y"), inplace=True)

st.sidebar.header("Homesick® by Kunal")

# **🔹 Sidebar Logo**
st.sidebar.image("C:/Users/karti/dashboard/Homesick_logo.jpeg", use_container_width=True)

# **🔹 Sidebar - Next & Overdue Payments**
st.sidebar.subheader("📌 Upcoming & Overdue Payments")

if "Remaining Payment" in df_artists.columns and "Total Payment Status" in df_artists.columns:
    forecast_df = df_artists[
        ["Artist Name", "Remaining Forecast Payment Date", "Remaining Payment", "Total Payment Status"]
    ].dropna()

    forecast_df = forecast_df[forecast_df["Total Payment Status"].str.lower() != "complete"]
    today = datetime.date.today()
    forecast_df["Remaining Forecast Payment Date"] = pd.to_datetime(forecast_df["Remaining Forecast Payment Date"], errors='coerce')

    overdue_payments = forecast_df[forecast_df["Remaining Forecast Payment Date"].dt.date < today]
    future_payments = forecast_df[forecast_df["Remaining Forecast Payment Date"].dt.date >= today]

    # **🔴 Show Overdue Payments in Sidebar**
    if not overdue_payments.empty:
        st.sidebar.write("🔴 **Overdue Payments**")
        for _, row in overdue_payments.iterrows():
            st.sidebar.markdown(
                f"<p style='color: red;'>🚨 {row['Artist Name']} - ${row['Remaining Payment']:,.2f} (Due: {row['Remaining Forecast Payment Date'].strftime('%d-%b-%Y')})</p>",
                unsafe_allow_html=True
            )

    # **🔜 Show All Next Payments in Sidebar**
    if not future_payments.empty:
        st.sidebar.write("🔜 **Next Payments Due**")
        for _, row in future_payments.iterrows():
            st.sidebar.write(f"📅 {row['Artist Name']} - ${row['Remaining Payment']:,.2f} on {row['Remaining Forecast Payment Date'].strftime('%d-%b-%Y')}")

# **🔹 Dashboard Title**
st.title("Expense Tracker")

# **🔹 Overview Metrics**
total_expense = df_expenses["Amount Adjusted for D/C"].sum()
total_num_artists = df_artists[df_artists["Employment"].str.upper() == "Y"]["Artist Name"].nunique()

# **🔹 Convert 'Remaining Forecast Payment Date' to Proper Datetime Format**
df_artists["Remaining Forecast Payment Date"] = pd.to_datetime(df_artists["Remaining Forecast Payment Date"], errors='coerce')

# **🔹 Get Current Month & Year**
current_month = datetime.date.today().strftime("%B %Y")

# **🔹 Filter for Total Amount Due in the Current Month**
total_due_this_month = df_artists[
    (df_artists["Remaining Forecast Payment Date"].dt.strftime("%B %Y") == current_month) &
    (df_artists["Total Payment Status"].str.lower() != "complete")
]

# **🔹 Ensure 'Total Amount Due' is Numeric Before Summing**
df_artists["Total Amount Due"] = pd.to_numeric(df_artists["Total Amount Due"], errors='coerce')

# **🔹 Calculate Total Amount Due**
total_amount_due = total_due_this_month["Total Amount Due"].sum() if not total_due_this_month.empty else 0

# **🔹 Display in Overview Metrics**
st.metric("Total Expenses", f"${total_expense:,.2f}")
st.metric("Total Number of Active Artists", f"{total_num_artists}")
st.metric(f"Total Amount Due ({current_month})", f"${total_amount_due:,.2f}")


# **🔹 Last Month's Overview**
today = datetime.date.today()
first_day_of_this_month = datetime.date(today.year, today.month, 1)
last_month = (first_day_of_this_month - datetime.timedelta(days=1)).strftime("%B %Y")
previous_month = (first_day_of_this_month - datetime.timedelta(days=32)).strftime("%B %Y")

# Filter for Last Month and Previous Month
last_month_expenses = df_expenses[df_expenses["Month"] == last_month]
previous_month_expenses = df_expenses[df_expenses["Month"] == previous_month]

# **Total Spent Last Month**
last_month_spent = last_month_expenses["Amount Adjusted for D/C"].sum()
previous_month_spent = previous_month_expenses["Amount Adjusted for D/C"].sum() if not previous_month_expenses.empty else None

# **Calculate Increase/Decrease**
if previous_month_spent is not None:
    pnl_display = last_month_spent - previous_month_spent
else:
    pnl_display = "N/A"

# **Most Expensive Category Last Month**
if not last_month_expenses.empty:
    most_expensive_category = last_month_expenses.groupby("Category")["Amount Adjusted for D/C"].sum().idxmax()
    most_expensive_category_amount = last_month_expenses.groupby("Category")["Amount Adjusted for D/C"].sum().max()
else:
    most_expensive_category = "N/A"
    most_expensive_category_amount = 0

# **🔹 Display Last Month's Overview**
st.subheader("📊 Last Month's Overview")
st.write(f"**Month:** {last_month}")
st.write(f"**Net:** ${last_month_spent:,.2f}")
st.write(f"**Most Expensive Category:** {most_expensive_category} (${most_expensive_category_amount:,.2f})")
st.write(f"**PnL Change from Last Month:** ${pnl_display:,.2f}" if pnl_display != "N/A" else "**PnL Change from Last Month:** N/A")

# **🔹 Selected Month Filter**
available_months = sorted(
    df_expenses["Month"].dropna().unique(),
    key=lambda x: (datetime.datetime.strptime(x, "%B %Y").year, datetime.datetime.strptime(x, "%B %Y").month)
)

selected_month = st.selectbox("Filter by Month:", ["All"] + available_months)

if selected_month == "All":
    df_expenses_filtered = df_expenses
    df_artists_filtered = df_artists
else:
    df_expenses_filtered = df_expenses[df_expenses["Month"] == selected_month]
    df_artists_filtered = df_artists[df_artists["Month"] == selected_month]

# **🔹 Breakdown by Category (Pie Chart)**

total_spent_this_month = df_expenses_filtered["Amount Adjusted for D/C"].sum() # Total Spent
artist_spent_this_month = df_artists_filtered["Total Amount Paid"].sum() # Total Spent per Artist

expense_by_category = df_expenses_filtered.groupby("Category")["Amount Adjusted for D/C"].sum().reset_index()
fig_category = px.pie(expense_by_category, names="Category", values="Amount Adjusted for D/C", title=f"Expenses by Category ({selected_month})")
# Customize hover and text to display dollar values instead of percentages
fig_category.update_traces(
    textinfo="label+value",  # Show the label and dollar value on the chart
    hovertemplate='%{label}: $%{value:,.2f}<extra></extra>'  # Customize hover to show dollar value
)

st.subheader(f"Total Expense Breakdown ({selected_month})")
st.write(f"Total Spent ({selected_month}) = ${total_spent_this_month:,.2f}")
st.write(f"Total Spent on Artists ({selected_month}) = ${artist_spent_this_month:,.2f}")
st.plotly_chart(fig_category)

# **🔹 Breakdown by Vendor (Pie Chart)**
expense_by_vendor = df_expenses_filtered.groupby("Vendor/Supplier")["Amount Adjusted for D/C"].sum().reset_index()
fig_vendor = px.pie(expense_by_vendor, names="Vendor/Supplier", values="Amount Adjusted for D/C", title=f"Expenses by Vendor ({selected_month})")
# Customize hover and text to display dollar values
fig_vendor.update_traces(
    textinfo="label+value",
    hovertemplate='%{label}: $%{value:,.2f}<extra></extra>'
)
st.subheader(f"Expenses by Vendor ({selected_month})")
st.plotly_chart(fig_vendor)

# **🔹 Breakdown by Artist (Bar Chart)**
expense_by_name = df_artists_filtered.groupby("Artist Name")["Total Payment"].sum().reset_index()
fig_bar = px.bar(expense_by_name, x="Artist Name", y="Total Payment", title=f"Expenses per Artist ({selected_month})", labels={"Total Payment": "Total Expense ($)"})
st.subheader(f"Artist Expense Breakdown ({selected_month})")
st.plotly_chart(fig_bar)

# **🔹 Display Tables Based on Layout Selection**
st.subheader(f"💾 Expense Data ({selected_month})")
st.dataframe(df_expenses_filtered)
st.subheader(f"💾 Artist Payment Data ({selected_month})")
st.dataframe(df_artists_filtered)

