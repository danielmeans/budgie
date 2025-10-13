# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Budgie is a personal spending tracker built with Streamlit. It ingests bank transaction CSVs from multiple banks (Chase, Capital One), normalizes them into a common format, and provides visualization and analysis of spending patterns.

## Running the Application

```bash
# Install dependencies (use uv for package management)
uv pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

## Key Architecture

### Bank CSV Normalization System

The app uses a **bank detection and normalization pipeline** to handle different bank CSV formats:

1. **Bank Detection** (`detect_bank()` in app.py:99-113): Identifies bank format by inspecting column names
2. **Bank-specific Normalizers**: Each bank has a normalizer function that maps its columns to a standard schema
3. **Standard Schema**: All transactions are normalized to: `['date', 'description', 'category', 'amount', 'account']`

#### Supported Banks

- **Chase**: Two format variations (old/new) with different column names
  - Multiplies `amount` by -1 to normalize sign convention
  - Normalizer: `normalize_chase()` (app.py:37-80)

- **Capital One**: Uses separate Debit/Credit columns
  - Combines Debit and Credit into single `amount` (Debit - Credit)
  - Normalizer: `normalize_capone()` (app.py:82-96)

#### Adding New Banks

To add support for a new bank:
1. Define column mapping dictionary (similar to `CAPONE_MAP` at app.py:28-34)
2. Create normalizer function that returns standard schema
3. Add bank detection logic to `detect_bank()`
4. Register normalizer in `normalizers` dict (app.py:115-118)

### Transaction Filtering

**Payment Filtering** (app.py:124-130, 171-177): Automatically excludes credit card payments and reversals by matching description text against `PAYMENT_PHRASES` list. This prevents double-counting of transfers between accounts.

**Category Mapping** (app.py:132-145): Maps bank-provided categories to simplified grouped categories for cleaner visualizations.

### Multi-Page Structure

The app has two main pages (selected via sidebar radio at app.py:148):

1. **Dashboard** (app.py:178-277):
   - Monthly summary metrics (spending, income, net)
   - Category breakdown visualizations (pie/bar charts)
   - Filterable transaction table

2. **Spending Over Time** (app.py:278-312):
   - Time-series stacked bar chart
   - Configurable granularity (Month/Day)
   - Shows spending trends by category

## Utilities

### Interactive Transaction Categorizer

`src/categorize_transactions.py` is a CLI tool for manually categorizing transactions:

```bash
python src/categorize_transactions.py <input_csv> <output_csv>
```

Interactive prompts guide user through categorizing each transaction. Progress can be saved mid-session with 's' command.

## Development Notes

- **Data Directories**: Multiple transaction folders exist (`personal_transactions/`, `shared_transactions/`, etc.) - these contain user data and should not be committed
- **Date Handling**: The app includes robust date parsing with error handling and warnings for invalid dates (app.py:48-51, 92-95)
- **Debugging**: Dashboard page includes optional debug info display (app.py:268-272) and account breakdown logging (app.py:256-265)
