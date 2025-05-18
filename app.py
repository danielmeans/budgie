import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Spending Tracker", layout="wide")
st.title("Personal Spending Tracker")
st.sidebar.title("Navigation")

# --- Bank column mappings ---
CHASE_MAPS = [
    # Old Chase format
    {
        "Trans Date": "date",
        "Description": "description",
        "Category": "category",
        "Amount": "amount"
    },
    # New Chase format
    {
        "Transaction Date": "date",
        "Description": "description",
        "Category": "category",
        "Amount": "amount"
    }
]
CAPONE_MAP = {
    "Transaction Date": "date",
    "Description": "description",
    "Category": "category",
    "Debit": "debit",
    "Credit": "credit"
}

# --- Normalizer functions ---
def normalize_chase(df):
    # Try all Chase mappings
    for mapping in CHASE_MAPS:
        if all(col in df.columns for col in mapping.keys()):
            df = df.rename(columns=mapping)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce') * -1
            df['account'] = 'Chase'
            for col in ['category', 'description']:
                if col not in df:
                    df[col] = None
            return df[['date', 'description', 'category', 'amount', 'account']]
    raise ValueError("No valid Chase mapping found")

def normalize_capone(df):
    df = df.rename(columns=CAPONE_MAP)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['debit'] = pd.to_numeric(df.get('debit', 0), errors='coerce').fillna(0)
    df['credit'] = pd.to_numeric(df.get('credit', 0), errors='coerce').fillna(0)
    df['amount'] = df['debit'] - df['credit']
    df['account'] = 'Capital One'
    for col in ['category', 'description']:
        if col not in df:
            df[col] = None
    return df[['date', 'description', 'category', 'amount', 'account']]

# --- Bank detection ---
def detect_bank(df):
    # Chase: either 'Trans Date' or 'Transaction Date' + 'Amount' + 'Description'
    if  "Amount" in df.columns:
        return "chase"
    elif "Debit" in df.columns:
        return "capone"
    else:
        return "unknown"

normalizers = {
    "chase": normalize_chase,
    "capone": normalize_capone
}

# --- File uploader and normalization ---
uploaded_files = st.file_uploader("Upload CSVs (Chase, Capital One)", type="csv", accept_multiple_files=True)
all_data = pd.DataFrame()

PAYMENT_PHRASES = [
    "autopay pymt",
    "payment thank you",
    "automatic payment",
    "returned payment",
    "reversal"
]

CATEGORY_MAP = {
    'Groceries': 'Groceries',
    'Food & Drink': 'Dining Out',
    'Shopping': 'Shopping',
    'Merchandise': 'Shopping',
    'Personal': 'Personal/Health',
    'Health & Wellness': 'Personal/Health',
    'Education': 'Personal/Health',
    'Insurance': 'Bills & Utilities',
    'Internet': 'Bills & Utilities',
    'Gas': 'Auto & Travel',
    'Automotive': 'Auto & Travel',
    'Travel': 'Auto & Travel'
}

# --- Page selection ---
page = st.sidebar.radio("Page", ["Dashboard", "Spending Over Time"])

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        bank = detect_bank(df)
        if bank in normalizers:
            try:
                norm_df = normalizers[bank](df)
                norm_df['grouped_category'] = norm_df['category'].map(CATEGORY_MAP).fillna('Other')
                dfs.append(norm_df)
            except Exception as e:
                st.warning(f"Error normalizing {file.name}: {e}")
        else:
            st.warning(f"Unknown format for file: {file.name}")
    if dfs:
        all_data = pd.concat(dfs, ignore_index=True)
        # Filter out payment/reversal rows
        def is_payment_row(description):
            if pd.isna(description):
                return False
            desc = str(description).lower()
            return any(phrase in desc for phrase in PAYMENT_PHRASES)
        mask = all_data['description'].apply(lambda x: not is_payment_row(x))
        all_data = all_data[mask]
        if page == "Dashboard":
            # --- Monthly Summary ---
            all_data['month'] = all_data['date'].dt.to_period('M').astype(str)
            months = sorted(all_data['month'].unique(), reverse=True)
            selected_month = st.sidebar.selectbox("Month", months)
            month_df = all_data[all_data['month'] == selected_month]
            spending = month_df[month_df['amount'] > 0]['amount'].sum()
            income = -month_df[month_df['amount'] < 0]['amount'].sum()
            net = income - spending
            st.subheader(f"Summary for {selected_month}")
            st.metric("Spending", f"${spending:,.2f}")
            st.metric("Income", f"${income:,.2f}")
            st.metric("Net", f"${net:,.2f}")
            # --- Category Breakdown Visualization ---
            st.subheader("Category Breakdown")
            chart_type = st.radio("Chart type", ["Pie Chart", "Bar Chart"], horizontal=True)
            cat_sum = month_df[month_df['amount'] > 0].groupby('grouped_category')['amount'].sum().reset_index()
            if not cat_sum.empty:
                if chart_type == "Pie Chart":
                    fig = px.pie(
                        cat_sum,
                        names='grouped_category',
                        values='amount',
                        title='Spending by Category',
                        hole=0.3
                    )
                    fig.update_traces(textinfo='percent+label+value', texttemplate='%{label}<br>%{percent} ($%{value:,.0f})')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.bar(
                        cat_sum,
                        x='grouped_category',
                        y='amount',
                        text='amount',
                        labels={'amount': 'Spending', 'grouped_category': 'Category'},
                        title='Spending by Category'
                    )
                    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                    fig.update_layout(yaxis_title='Spending', xaxis_title='Category', uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expenses for this month to display.")
            # --- Filtering UI ---
            if not all_data.empty:
                # Date range filter
                date_min, date_max = all_data['date'].min(), all_data['date'].max()
                date_range = st.sidebar.date_input("Date range", [date_min, date_max])
                # Category filter
                categories = ["All"] + sorted(all_data['grouped_category'].dropna().unique())
                category = st.sidebar.selectbox("Category", categories)
                # Apply filters
                filtered = all_data[
                    (all_data['date'] >= pd.to_datetime(date_range[0])) &
                    (all_data['date'] <= pd.to_datetime(date_range[1]))
                ]
                if category != "All":
                    filtered = filtered[filtered['grouped_category'] == category]
                st.subheader("Filtered Transactions")
                st.dataframe(filtered)
            else:
                st.subheader("Unified Transactions Table")
                st.dataframe(all_data)
        elif page == "Spending Over Time":
            st.header("Spending Over Time")
            df_exp = all_data[all_data['amount'] > 0].copy()
            # Sidebar controls for this page
            date_min, date_max = df_exp['date'].min(), df_exp['date'].max()
            date_range = st.sidebar.date_input("Date range (Spending Over Time)", [date_min, date_max])
            granularity = st.sidebar.radio("Granularity", ["Month", "Day"], horizontal=True)
            # Filter by date range
            mask = (df_exp['date'] >= pd.to_datetime(date_range[0])) & (df_exp['date'] <= pd.to_datetime(date_range[1]))
            df_exp = df_exp[mask]
            # Group by selected granularity
            if granularity == "Month":
                df_exp['period'] = df_exp['date'].dt.to_period('M').astype(str)
            else:
                df_exp['period'] = df_exp['date'].dt.date.astype(str)
            grouped = df_exp.groupby(['period', 'grouped_category'])['amount'].sum().reset_index()
            totals = df_exp.groupby('period')['amount'].sum().reset_index()
            fig = px.bar(
                grouped,
                x='period',
                y='amount',
                color='grouped_category',
                labels={'amount': 'Spending', 'period': granularity, 'grouped_category': 'Category'},
                title=f'Spending by {granularity}'
            )
            fig.add_trace(go.Scatter(
                x=totals['period'],
                y=totals['amount'],
                text=[f"${v:,.0f}" for v in totals['amount']],
                mode='text',
                textposition='top center',
                showlegend=False
            ))
            fig.update_layout(barmode='stack', xaxis={'categoryorder':'category ascending'})
            st.plotly_chart(fig, use_container_width=True) 