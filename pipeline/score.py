
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

# Configuration
INPUT_DIR = 'processed_data'
OUTPUT_DIR = 'processed_data' # Saving back to processed
SCORING_WEIGHTS = {
    'default_rate': 0.4,
    'avg_delay': 0.3,
    'volatility': 0.2,
    'country_risk': 0.1
}

def load_data():
    invoices = pd.read_csv(os.path.join(INPUT_DIR, 'invoices_enriched.csv'))
    exporters = pd.read_csv(os.path.join(INPUT_DIR, 'exporters_scored.csv'))
    return invoices, exporters

def calculate_country_risk(invoices_df):
    """
    Calculates a risk score for each country based on historical default rates.
    """
    country_stats = invoices_df.groupby('importer_country').agg(
        total_txns=('invoice_id', 'count'),
        default_count=('is_defaulted', 'sum')
    )
    country_stats['country_risk_score'] = country_stats['default_count'] / country_stats['total_txns']
    return country_stats['country_risk_score'].to_dict()

def normalize_features(df, features):
    """
    Normalizes selected features to a 0-1 range using Min-Max Scaling.
    """
    scaler = MinMaxScaler()
    df_scaled = df.copy()
    df_scaled[features] = scaler.fit_transform(df[features])
    return df_scaled

def calculate_risk_score(row, weights):
    """
    Computes the weighted risk score (0-100).
    """
    score = (
        (row['norm_default_rate'] * weights['default_rate']) +
        (row['norm_avg_delay'] * weights['avg_delay']) +
        (row['norm_volatility'] * weights['volatility']) +
        (row['norm_country_risk'] * weights['country_risk'])
    ) * 100
    return round(score, 2)

def categorize_risk(score):
    if score < 30:
        return 'Low'
    elif score < 70:
        return 'Medium'
    else:
        return 'High'

def generate_explanation(row):
    """
    Generates a human-readable explanation for the risk score.
    """
    factors = []
    if row['norm_default_rate'] > 0.7:
        factors.append(f"High historical default rate ({row['default_rate_raw']:.1%})")
    if row['norm_avg_delay'] > 0.7:
        factors.append(f"Frequent payment delays ({row['avg_delay_raw']:.1f} days avg)")
    if row['norm_volatility'] > 0.8:
        factors.append("Unusual invoice amount (high volatility)")
    if row['norm_country_risk'] > 0.7:
        factors.append(f"High-risk importer country ({row['importer_country']})")
    
    if not factors:
        return "Standard risk profile. No major red flags."
    return "Risk Drivers: " + "; ".join(factors)

def main():
    print("--- Starting Risk Engine ---")
    invoices, exporters = load_data()
    
    # 1. Prepare Data
    # We need to map exporter-level traits (Default Rate, Avg Delay) to Invoices
    # And calculate Country Risk from Invoices
    
    # Map Exporter Features
    # Note: 'invoice_amount_std' in exporters is volatility, but for the specific invoice, 
    # we already calculated 'amt_vs_avg_ratio' in ETL pipeline which is a better 'per-invoice' volatility measure.
    # However, the prompt asks for "Invoice Amount Volatility", let's use the Ratio we calculated.
    
    # Merge Exporter Stats
    risk_df = pd.merge(invoices, exporters[['exporter_id', 'default_rate', 'avg_payment_delay']], on='exporter_id', how='left')
    
    # Map Country Risk
    country_risk_map = calculate_country_risk(invoices)
    risk_df['country_risk_raw'] = risk_df['importer_country'].map(country_risk_map)
    
    # Rename for clarity before normalization
    risk_df = risk_df.rename(columns={
        'amt_vs_avg_ratio': 'volatility_raw',
        'default_rate': 'default_rate_raw',
        'avg_payment_delay': 'avg_delay_raw'
    })
    
    # Fill NA just in case
    risk_df = risk_df.fillna(0)

    # 2. Normalize
    print("Normalizing Metrics...")
    # These are the columns we want to squash to 0-1
    feature_cols = ['default_rate_raw', 'avg_delay_raw', 'volatility_raw', 'country_risk_raw']
    norm_cols = ['norm_default_rate', 'norm_avg_delay', 'norm_volatility', 'norm_country_risk']
    
    scaler = MinMaxScaler()
    risk_df[norm_cols] = scaler.fit_transform(risk_df[feature_cols])
    
    # 3. Calculate Score
    print("Calculating Weighted Risk Scores...")
    risk_df['risk_score'] = risk_df.apply(lambda x: calculate_risk_score(x, SCORING_WEIGHTS), axis=1)
    
    # 4. Categorize
    risk_df['risk_category'] = risk_df['risk_score'].apply(categorize_risk)
    
    # 5. Explain
    risk_df['risk_explanation'] = risk_df.apply(generate_explanation, axis=1)
    
    # Select clean columns for output
    output_columns = [
        'invoice_id', 'exporter_id', 'importer_country', 'invoice_amount', 
        'risk_score', 'risk_category', 'risk_explanation',
        'default_rate_raw', 'avg_delay_raw', 'volatility_raw', 'country_risk_raw'
    ]
    
    final_df = risk_df[output_columns]
    
    # Save
    output_path = os.path.join(OUTPUT_DIR, 'invoices_scored.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"Scoring Complete. Saved to {output_path}")
    print("\nSample High Risk Invoices:")
    print(final_df.sort_values('risk_score', ascending=False).head(5)[['invoice_id', 'risk_score', 'risk_category', 'risk_explanation']])

if __name__ == "__main__":
    main()
