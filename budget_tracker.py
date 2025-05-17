import streamlit as st 
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import base64
import plotly.graph_objects as go
import plotly.express as px

# --- Page Config & Dark Mode ---
st.set_page_config(page_title="HOMESICK® Budget Tracker", layout="wide")

# --- Custom CSS Styling ---
st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    * {
    font-family: 'Avenir', sans-serif !important;
    }                
    header[data-testid="stHeader"] {
    background-color: #1e1e1e;
    color: white;
    }
    header[data-testid="stHeader"] {
    display: none;
    }                      
    section[data-testid="stSidebar"] {
        background-color: #1e1e1e;
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: white;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background-color: white !important;
        color: black !important;
    }
    section[data-testid="stSidebar"] .stSelectbox input {
        color: black !important;
    }
    section[data-testid="stSidebar"] .stSelectbox div[role="option"] {
        color: black !important;
        background-color: white !important;
    }
    section[data-testid="stSidebar"] .stSelectbox svg {
        color: black !important;
    }
    div.stDownloadButton > button {
        background-color: white;
        color: black;
        border: 1px solid black;
        border-radius: 5px;
        padding: 0.5em 1.1em;
        font-weight: bold;
    }
    div.stDownloadButton > button:hover {
        background-color: #f0f0f0;
        color: black;
    }
    body, .stApp {
        background-color: #1e1e1e;
        color: white;
    }
    h1, h2, h3, h4, h5, h6, p, div {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- Password Protection with Logout ---
PASSWORD = "homesick2024"  # 🔐 Set your desired password

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Handle logout
if st.sidebar.button("🔓"):
    st.session_state.authenticated = False
    st.rerun()

# Authentication gate
if not st.session_state.authenticated:
    st.title("🔐 HOMESICK® Dashboard Login")
    input_pwd = st.text_input("Enter Password", type="password")
    if st.button("🔑"):
        if input_pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()  # Halt execution if not authenticated

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Custom Branded Header ---
st.markdown("""
    <div style="
        background-color: #1e1e1e;
        padding: 1rem 2rem;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #444;
    ">
        <h2 style="color: white; margin: 0;">HOMESICK® By Kunal</h2>
    </div>
""", unsafe_allow_html=True)

# --- Month mapping ---
month_name_to_number = {name: num for num, name in enumerate([
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'], 1)}

# --- Load Data ---
@st.cache_data
def load_data():
    xls = pd.ExcelFile("Homesick Budget Tracker.xlsx")
    total_spend_df = xls.parse("Total Spend")
    artist_tracker_df = xls.parse("Artist Tracker")

    total_spend_df['Date'] = pd.to_datetime(total_spend_df['Date'])
    total_spend_df['Month'] = total_spend_df['Date'].dt.month_name()
    total_spend_df['Year'] = total_spend_df['Date'].dt.year

    artist_tracker_df['Advance Payment Date'] = pd.to_datetime(artist_tracker_df['Advance Payment Date'], errors='coerce')
    artist_tracker_df['Remaining Actual Payment Date'] = pd.to_datetime(artist_tracker_df['Remaining Actual Payment Date'], errors='coerce')
    artist_tracker_df['Effective Payment Date'] = artist_tracker_df['Advance Payment Date'].combine_first(
        artist_tracker_df['Remaining Actual Payment Date']
    )

    return total_spend_df, artist_tracker_df

total_spend_df, artist_tracker_df = load_data()

# --- Get Defaults ---
today = datetime.today()
default_year = today.year
default_month_name = today.strftime("%B")

# --- Tabs ---
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Visualize"])

# ----------------------------
# 📊 TAB 1: DASHBOARD
# ----------------------------
with tab1:
    with st.sidebar:

        st.image("Homesick_logo.jpeg")
        st.header("🔎 Filter Dashboard Data")

        year = st.select_slider("Select Year", options=sorted(total_spend_df['Year'].unique(), reverse=True), value=default_year)
        month = st.select_slider("Select Month", options=list(month_name_to_number.keys()), value=default_month_name)

    selected_month_num = month_name_to_number[month]
    selected_year = int(year)

    if selected_month_num == 1:
        prev_month = 12
        prev_year = selected_year - 1
    else:
        prev_month = selected_month_num - 1
        prev_year = selected_year

    prev_month_name = list(month_name_to_number.keys())[prev_month - 1]

    filtered_spend_df = total_spend_df[
        (total_spend_df['Date'].dt.month == selected_month_num) &
        (total_spend_df['Date'].dt.year == selected_year)
    ]

    if not filtered_spend_df.empty:
        top_category = filtered_spend_df.groupby('Category')['Amount Adjusted for D/C'].sum().idxmax()
        top_category_spend = filtered_spend_df.groupby('Category')['Amount Adjusted for D/C'].sum().max()
    else:
        top_category = "No data"
        top_category_spend = 0

    spend_this_month = filtered_spend_df['Amount Adjusted for D/C'].sum()

    spend_last_month = total_spend_df[
        (total_spend_df['Date'].dt.month == prev_month) &
        (total_spend_df['Date'].dt.year == prev_year)
    ]['Amount Adjusted for D/C'].sum()

    pnl_change = spend_this_month - spend_last_month

    filtered_artist_df = artist_tracker_df[
        (artist_tracker_df['Effective Payment Date'].dt.month == selected_month_num) &
        (artist_tracker_df['Effective Payment Date'].dt.year == selected_year)
    ]

    filtered_total_artist_spend = filtered_artist_df['Total Amount Paid'].sum()

    if not filtered_artist_df.empty:
        filtered_most_expensive_artist = filtered_artist_df.groupby('Artist Name')['Total Amount Paid'].sum().idxmax()
        filtered_most_expensive_artist_spend = filtered_artist_df.groupby('Artist Name')['Total Amount Paid'].sum().max()
    else:
        filtered_most_expensive_artist = "N/A"
        filtered_most_expensive_artist_spend = 0

    total_spend_to_date = total_spend_df['Amount Adjusted for D/C'].sum()

    st.markdown("<h1 style='text-align: center;'>💵 Spending</h1>", unsafe_allow_html=True)
    st.markdown("---")

    if filtered_spend_df.empty:
        st.warning(f"No spend data available for {month} {year}.")

    def render_metric(title, value):
    # Determine value color based on type and value
        if isinstance(value, (int, float)):
            color = "#ff4d4d" if value > 0 else "#00cc66"
            value_str = f"${value:,.2f}"
        else:
            color = "#1F51FF"
            value_str = value

        return f"""
            <div style='
                border: 1px solid #aaa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                background-color: #2e2e2e;
            '>
                <h4 style='margin-bottom: 5px; color: #FFFFFF;'>{title}</h4>
                <p style='font-size: 24px; font-weight: bold; color: {color};'>{value_str}</p>
            </div>
        """

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(render_metric(f"Total Spend to Date", total_spend_to_date), unsafe_allow_html=True)
        st.markdown(render_metric(f"Top Spending Category ({month})", top_category), unsafe_allow_html=True)
        st.markdown(render_metric(f"Top Spending Category ($) ({month})", top_category_spend), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric(f"Total Spend for ({month})", spend_this_month), unsafe_allow_html=True)
        st.markdown(render_metric(f"Total Spend Last Month ({prev_month_name})", spend_last_month), unsafe_allow_html=True)
        st.markdown(render_metric(f"Net Change from Last Month", pnl_change), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric(f"Total Spend for Artists ({month})", filtered_total_artist_spend), unsafe_allow_html=True)
        st.markdown(render_metric(f"Most Expensive Artist ({month})", filtered_most_expensive_artist), unsafe_allow_html=True)
        st.markdown(render_metric(f"Most Expensive Artist ($) ({month})", filtered_most_expensive_artist_spend), unsafe_allow_html=True)

    # --- PDF Export ---
    def clean_text(text):
        return str(text).encode("ascii", "ignore").decode("ascii")

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text(f"HOMESICK Budget Summary - {month} {year}"), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.ln(5)
        pdf.cell(0, 10, clean_text(f"Total Spend to Date: ${total_spend_to_date:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Top Spending Category: {top_category}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Top Spending Category ($): ${top_category_spend:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Total Spent in {month} {year}: ${spend_this_month:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Total Spent in {prev_month_name} {prev_year}: ${spend_last_month:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"PNL Change: ${pnl_change:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Total Spend on Artists: ${filtered_total_artist_spend:,.2f}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Most Expensive Artist: {filtered_most_expensive_artist}"), ln=True)
        pdf.cell(0, 10, clean_text(f"Most Expensive Artist ($): ${filtered_most_expensive_artist_spend:,.2f}"), ln=True)
        return pdf.output(dest='S').encode('latin1')

    def get_pdf_download_link(pdf_bytes, filename):
        b64 = base64.b64encode(pdf_bytes).decode()
        return f'''
            <a href="data:application/pdf;base64,{b64}" download="{filename}">
                <button style="
                    background-color: white;
                    color: black;
                    border: 1px solid black;
                    border-radius: 6px;
                    padding: 0.5em 1.1em;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 1em;
                ">
                    📥 Download PDF
                </button>
            </a>
        '''

    st.markdown("---")
    st.subheader("📄 Export Report")
    st.markdown(get_pdf_download_link(generate_pdf(), f"budget_summary_{month}_{year}.pdf"), unsafe_allow_html=True)

# Visualize tab would follow here (not shown to avoid message overflow).
# --- TAB 2: VISUALIZE ---
with tab2:
    st.markdown("<h1 style='text-align: center;'>📈 Visualizations</h1>", unsafe_allow_html=True)

    text_color = "white"
    bg_color = "#1e1e1e"

    # --- Spend by Category ---
    st.subheader("Spend by Category")
    category_df = total_spend_df.groupby('Category')['Amount Adjusted for D/C'].sum().reset_index()
    category_df = category_df.sort_values(by='Amount Adjusted for D/C', ascending=True)

    fig_cat = go.Figure(go.Bar(
        x=category_df['Amount Adjusted for D/C'],
        y=category_df['Category'],
        orientation='h',
        marker_color='#4c9aff',
        text=[f"${x:,.2f}" for x in category_df['Amount Adjusted for D/C']],
        textposition='outside'
    ))

    fig_cat.update_layout(
        title="Category Spending",
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font_color=text_color,
        xaxis=dict(
            title="Amount ($)",
            color=text_color,
            gridcolor="gray",
            nticks=10,
            showline=True,
            ticks="outside"
        ),
        yaxis=dict(title="", color=text_color),
        height=500
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    # --- Monthly Spend Over Time ---
    st.subheader("Monthly Spend Over Time")
    monthly_trend = total_spend_df.copy()
    monthly_trend['Month-Year'] = monthly_trend['Date'].dt.to_period('M').astype(str)
    monthly_df = monthly_trend.groupby('Month-Year')['Amount Adjusted for D/C'].sum().reset_index()

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=monthly_df['Month-Year'],
        y=monthly_df['Amount Adjusted for D/C'],
        mode='lines+markers',
        line=dict(color='#00cc99', width=3),
        marker=dict(color='white', size=8),
        text=[f"${x:,.2f}" for x in monthly_df['Amount Adjusted for D/C']],
        hovertemplate='%{x}: %{text}<extra></extra>'
    ))

    fig_line.update_layout(
        title="Monthly Spending Trend",
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font_color=text_color,
        xaxis=dict(
            title="Month-Year",
            tickangle=-45,
            color=text_color,
            gridcolor="gray",
            nticks=20,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title="Amount ($)",
            color=text_color,
            gridcolor="gray",
            nticks=10,
            showline=True,
            ticks="outside"
        ),
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Top 5 Artists (Pie) ---
    st.subheader("Top 5 Artists by Spend")
    top_artists = artist_tracker_df.groupby('Artist Name')['Total Amount Paid'].sum().nlargest(5).reset_index()

    fig_pie = go.Figure(data=[go.Pie(
        labels=top_artists['Artist Name'],
        values=top_artists['Total Amount Paid'],
        hole=0.45,
        marker=dict(colors=px.colors.sequential.Blues[::-1]),
        textinfo='label+value',
        texttemplate="%{label}<br>$%{value:,.0f}",
        hovertemplate='%{label}: $%{value:,.2f}<extra></extra>',
        textfont=dict(color=text_color, size=14)
    )])

    fig_pie.update_layout(
        title="Top 5 Artists (by Spend)",
        showlegend=False,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color),
        height=500
    )
    st.plotly_chart(fig_pie, use_container_width=True)
