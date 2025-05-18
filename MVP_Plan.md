# Personal Spending Tracker MVP – To-Do List

- [x] **1. Project Setup**
    - Create project directory
    - Set up virtual environment
    - Install dependencies: `streamlit`, `pandas`, `matplotlib` or `plotly`, (Optional) `openpyxl`

- [x] **2. Basic Streamlit App Skeleton**
    - Create `app.py`
    - Add Streamlit page title and sidebar
    - Test app runs with `streamlit run app.py`

    **Sample Code:**
    ```python
    import streamlit as st
    st.set_page_config(page_title="Spending Tracker", layout="wide")
    st.title("Personal Spending Tracker")
    st.sidebar.title("Navigation")
    ```

- [x] **3. CSV Import Feature**
    - Add file uploader widget (multiple files)
    - Parse uploaded CSVs with pandas
    - Normalize columns (combine Debit/Credit into Amount, parse dates, etc.)
    - Aggregate expenses from all files
    - Display raw transactions table
    - Normalize to a standard schema
    - Filter out payment/reversal records by description

    **Sample Code:**
    ```python
    # ... see app.py for full implementation ...
    PAYMENT_PHRASES = [
        "autopay pymt",
        "payment thank you",
        "automatic payment",
        "returned payment",
        "reversal"
    ]
    def is_payment_row(description):
        if pd.isna(description):
            return False
        desc = str(description).lower()
        return any(phrase in desc for phrase in PAYMENT_PHRASES)
    mask = all_data['description'].apply(lambda x: not is_payment_row(x))
    all_data = all_data[mask]
    ```

- [x] **4. Transaction Table View**
    - Add sidebar widgets for date range and category
    - Filter `all_data` DataFrame based on user selections
    - Display the filtered DataFrame with `st.dataframe()`

    **Sample Code:**
    ```python
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
    ```

- [x] **5. Monthly Summary**
    - Add a month selector (sidebar)
    - Filter transactions for the selected month
    - Calculate and display:
        - Total spending for selected month
        - Total income for selected month
        - Net (income - spending)
    - Show summary at top of page using Streamlit metrics

    **Sample Code:**
    ```python
    if not all_data.empty:
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
    ```

- [ ] **6. Category Breakdown Visualization**
    - Use the filtered month_df for the selected month
    - Group by `grouped_category` and sum the `amount` (expenses only, i.e., amount > 0)
    - Display as a pie chart or bar chart (user can choose)
    - Use matplotlib or plotly for visualization
    - Show legend and values

    **Sample Code (Pie Chart):**
    ```python
    import matplotlib.pyplot as plt
    cat_sum = month_df[month_df['amount'] > 0].groupby('grouped_category')['amount'].sum()
    fig, ax = plt.subplots()
    ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%')
    st.pyplot(fig)
    ```
    **Sample Code (Bar Chart):**
    ```python
    import matplotlib.pyplot as plt
    cat_sum = month_df[month_df['amount'] > 0].groupby('grouped_category')['amount'].sum()
    fig, ax = plt.subplots()
    cat_sum.plot(kind='bar', ax=ax)
    ax.set_ylabel('Spending')
    st.pyplot(fig)
    ```
    **Sample Code (Plotly Bar):**
    ```python
    import plotly.express as px
    cat_sum = month_df[month_df['amount'] > 0].groupby('grouped_category')['amount'].sum().reset_index()
    fig = px.bar(cat_sum, x='grouped_category', y='amount', labels={'amount': 'Spending', 'grouped_category': 'Category'})
    st.plotly_chart(fig)
    ```

- [ ] **7. Budget Tracking (Simple)**
    - Allow user to set a monthly budget
    - Show progress bar of spending vs. budget
    - Highlight if over budget

    **Sample Code:**
    ```python
    budget = st.sidebar.number_input("Monthly Budget", min_value=0.0, value=2000.0)
    progress = min(spending / budget, 1.0)
    st.progress(progress, text=f"${spending:,.2f} / ${budget:,.2f}")
    if spending > budget:
        st.warning("Over budget!")
    ```

- [ ] **8. Export Feature**
    - Allow user to download filtered/processed data as CSV

    **Sample Code:**
    ```python
    import io
    csv = filtered.to_csv(index=False)
    st.download_button("Download Filtered Data", data=csv, file_name="filtered_transactions.csv", mime="text/csv")
    ```

- [ ] **9. Monthly Spending Over Time Visualization**
    - Add a new page or section for "Spending Over Time"
    - Group all transactions by month and category, summing the amount (expenses only)
    - Use Plotly to create a stacked bar chart:
        - X-axis: Month
        - Y-axis: Total spending
        - Color: Category (grouped_category)
    - Add interactive legend and tooltips
    - Optionally, allow toggling between "all categories" and "single category" view

    **Sample Code:**
    ```python
    import plotly.express as px

    # Prepare data
    df_exp = all_data[all_data['amount'] > 0].copy()
    df_exp['month'] = df_exp['date'].dt.to_period('M').astype(str)
    monthly = df_exp.groupby(['month', 'grouped_category'])['amount'].sum().reset_index()

    # Stacked bar chart
    fig = px.bar(
        monthly,
        x='month',
        y='amount',
        color='grouped_category',
        labels={'amount': 'Spending', 'month': 'Month', 'grouped_category': 'Category'},
        title='Monthly Spending by Category',
        text_auto='.2s'
    )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'category ascending'})
    st.plotly_chart(fig, use_container_width=True)
    ```

- [ ] **10. Polish & UX Improvements**
    - Responsive layout for mobile/desktop
    - Add helpful tooltips and instructions
    - Error handling for bad CSVs

    **Sample Code:**
    ```python
    try:
        # CSV parsing code
        pass
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
    ```

- [ ] **11. (Optional) Next Steps**
    - Manual category editing
    - Recurring expense detection
    - Multi-account support
    - User authentication (if needed)

- [ ] **12. Make transactions filterable by date range**
    - Add a date range filter to the transactions table view so users can filter transactions by any date span.

- [ ] **13. Allow transactions to have editable categories via dropdown**
    - Add a dropdown in the transaction table to allow users to edit the category of each transaction.
    - Save changes in memory (or persist if backend is added).

- [ ] **14. Add a column to exclude transactions from calculations**
    - Add a boolean column (e.g., 'Exclude') to the transaction table.
    - Transactions marked as excluded are ignored in all calculations and visualizations.

- [ ] **15. Explore secure/private deployment options**
    - Research and document ways to deploy the Streamlit app securely (e.g., password protection, VPN, self-hosting, Streamlit Community Cloud with access controls).
    - Ensure the app remains private and protected online.

---

> Follow this plan step by step, building and testing after each feature is added. 