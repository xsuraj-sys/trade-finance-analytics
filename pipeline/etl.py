
import pandas as pd
import numpy as np
import datetime
import os

# Configuration
DATA_DIR = 'data'
OUTPUT_DIR = 'processed_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    """Load raw CSV datasets."""
    try:
        exporters = pd.read_csv(os.path.join(DATA_DIR, 'exporters.csv'))
        invoices = pd.read_csv(os.path.join(DATA_DIR, 'invoices.csv'))
        transactions = pd.read_csv(os.path.join(DATA_DIR, 'transactions.csv'))
        print("Datasets loaded successfully.")
        return exporters, invoices, transactions
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return None, None, None

def clean_and_transform_invoices(invoices_df, transactions_df):
    """
    Clean dates, merge with transactions, and calculate payment delays.
    """
    print("Processing Invoices...")
    
    # helper for date parsing
    def parse_date(date_str):
        if pd.isna(date_str) or date_str == '':
            return pd.NaT
        return pd.to_datetime(date_str, errors='coerce').date()

    # 1. Date Conversion
    invoices_df['invoice_date'] = invoices_df['invoice_date'].apply(parse_date)
    invoices_df['due_date'] = invoices_df['due_date'].apply(parse_date)
    invoices_df['payment_date'] = invoices_df['payment_date'].apply(parse_date)

    # 2. Merge with Transactions to get actual payment details (if any)
    # We join on invoice_id. Note: Some invoices might not have transactions yet (open/defaulted without recovery).
    invoice_txn = pd.merge(invoices_df, transactions_df[['invoice_id', 'payment_amount']], 
                           on='invoice_id', how='left')

    # 3. Handle Missing Values / Defaults
    # If payment_amount is NaN, it implies 0.0 paid so far
    invoice_txn['payment_amount'] = invoice_txn['payment_amount'].fillna(0.0)

    # 4. Calculate Features
    
    # Days to Pay (Actual) - Only relevant if paid
    # Payment Delay: (Payment Date - Due Date). Positive = Late. Negative = Early.
    # If not paid, we can't calculate a definitive 'delay' for historical analysis, 
    # but for risk modeling of open invoices, current delay = Today - Due Date.
    
    today = datetime.date.today()
    
    def calculate_delay(row):
        if pd.notna(row['payment_date']):
            return (row['payment_date'] - row['due_date']).days
        else:
            # If not paid, and past due date, delay is running
            if today > row['due_date']:
                return (today - row['due_date']).days
            else:
                return 0 # Not due yet

    invoice_txn['payment_delay_days'] = invoice_txn.apply(calculate_delay, axis=1)

    # Feature: is_delayed (Binary). Strict threshold: > 0 days late.
    invoice_txn['is_delayed'] = invoice_txn['payment_delay_days'] > 0
    
    # Feature: is_defaulted (Binary). Logic: Status is 'Defaulted' or delay > 90 days
    invoice_txn['is_defaulted'] = (invoice_txn['status'] == 'Defaulted') | (invoice_txn['payment_delay_days'] > 90)

    return invoice_txn

def create_exporter_features(exporters_df, invoice_txn_df):
    """
    Aggregates invoice data to create rich exporter profiles.
    """
    print("Processing Exporter Profiles...")
    
    # Group by exporter
    exporter_stats = invoice_txn_df.groupby('exporter_id').agg(
        total_invoices=('invoice_id', 'count'),
        avg_invoice_amount=('invoice_amount', 'mean'),
        invoice_amount_std=('invoice_amount', 'std'), # volatility
        avg_payment_delay=('payment_delay_days', 'mean'),
        total_delayed_invoices=('is_delayed', 'sum'),
        total_defaulted_invoices=('is_defaulted', 'sum')
    ).reset_index()
    
    # Fill NaN for std (single invoice cases)
    exporter_stats['invoice_amount_std'] = exporter_stats['invoice_amount_std'].fillna(0)

    # Calculate Rates
    exporter_stats['delay_rate'] = exporter_stats['total_delayed_invoices'] / exporter_stats['total_invoices']
    exporter_stats['default_rate'] = exporter_stats['total_defaulted_invoices'] / exporter_stats['total_invoices']
    
    # Merge back to original exporter data to keep static fields (Country/Industry)
    final_exporters = pd.merge(exporters_df, exporter_stats, on='exporter_id', how='left')
    
    # Clean up redundant columns from original mock generation if they exist and recalculate ensures data integrity
    if 'total_invoices_x' in final_exporters.columns:
        final_exporters = final_exporters.drop(columns=['total_invoices_x', 'defaulted_invoices'])
        final_exporters = final_exporters.rename(columns={'total_invoices_y': 'total_invoices'})
        
    return final_exporters

def calculate_invoice_volatility(row, exporter_stats):
    """
    Feature: How much larger is this invoice compared to the exporter's average?
    High values might indicate unusual trading activity (riskier).
    """
    exp_stats = exporter_stats[exporter_stats['exporter_id'] == row['exporter_id']]
    if not exp_stats.empty:
        avg_amt = exp_stats.iloc[0]['avg_invoice_amount']
        if avg_amt > 0:
            return row['invoice_amount'] / avg_amt
    return 1.0

def main():
    exporters_raw, invoices_raw, transactions_raw = load_data()
    
    if exporters_raw is not None:
        # 1. Clean Invoices
        processed_invoices = clean_and_transform_invoices(invoices_raw, transactions_raw)
        
        # 2. Enrich Exporters
        processed_exporters = create_exporter_features(exporters_raw, processed_invoices)
        
        # 3. Add Volatility Feature to Invoices (Requires enriched exporter data)
        print("Calculating Invoice Volatility...")
        processed_invoices['amt_vs_avg_ratio'] = processed_invoices.apply(
            lambda x: calculate_invoice_volatility(x, processed_exporters), axis=1
        )

        # Save
        processed_invoices.to_csv(os.path.join(OUTPUT_DIR, 'invoices_enriched.csv'), index=False)
        processed_exporters.to_csv(os.path.join(OUTPUT_DIR, 'exporters_scored.csv'), index=False)
        
        print("\n--- ETL Pipeline Complete ---")
        print(f"Enriched Invoices: {len(processed_invoices)} records saved to {OUTPUT_DIR}/invoices_enriched.csv")
        print(f"Scored Exporters: {len(processed_exporters)} records saved to {OUTPUT_DIR}/exporters_scored.csv")
        
        # Display Sample Feature Importance
        print("\nTop 5 Riskiest Exporters (by Default Rate):")
        print(processed_exporters.sort_values(by='default_rate', ascending=False)[['exporter_id', 'industry', 'default_rate', 'avg_payment_delay']].head())

if __name__ == "__main__":
    main()
