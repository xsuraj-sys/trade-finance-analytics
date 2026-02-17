
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuration
INPUT_DIR = 'processed_data'
OUTPUT_REPORT_DIR = 'reports'
os.makedirs(OUTPUT_REPORT_DIR, exist_ok=True)

# Set the visualization style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def load_data():
    invoices = pd.read_csv(os.path.join(INPUT_DIR, 'invoices_enriched.csv'))
    exporters = pd.read_csv(os.path.join(INPUT_DIR, 'exporters_scored.csv'))
    return invoices, exporters

def plot_delay_by_country_industry(invoices, exporters, output_dir):
    print("Generating: Delay by Country/Industry...")
    
    # Merge invoices with exporter metadata (Industry, Country)
    merged_data = pd.merge(invoices, exporters[['exporter_id', 'industry', 'country']], on='exporter_id', how='left')

    # 1. Average Payment Delay by Importer Country
    plt.figure()
    avg_delay_country = merged_data.groupby('importer_country')['payment_delay_days'].mean().sort_values()
    sns.barplot(x=avg_delay_country.index, y=avg_delay_country.values, palette="viridis")
    plt.title('Average Payment Delay by Importer Country')
    plt.ylabel('Days (Avg)')
    plt.xlabel('Importer Country')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'delay_by_country.png'))
    plt.close()

    # 2. Average Payment Delay by Industry
    plt.figure()
    avg_delay_industry = merged_data.groupby('industry')['payment_delay_days'].mean().sort_values()
    # Using a different palette to distinguish
    sns.barplot(x=avg_delay_industry.index, y=avg_delay_industry.values, palette="magma")
    plt.title('Average Payment Delay by Exporter Industry')
    plt.ylabel('Days (Avg)')
    plt.xlabel('Industry')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'delay_by_industry.png'))
    plt.close()
    
    return merged_data

def analyze_amount_vs_delay(invoices, output_dir):
    print("Generating: Amount vs Delay Scatter...")
    
    plt.figure()
    # Filter out extreme outliers for better visualization if needed, but let's keep it raw for now
    sns.scatterplot(data=invoices, x='invoice_amount', y='payment_delay_days', alpha=0.6, hue='status')
    plt.title('Relationship: Invoice Amount vs. Payment Delay')
    plt.xlabel('Invoice Amount ($)')
    plt.ylabel('Payment Delay (Days)')
    plt.axhline(0, color='grey', linestyle='--') # On-time line
    plt.legend(title='Status')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'amount_vs_delay.png'))
    plt.close()

def identify_high_risk_exporters(exporters, output_dir):
    print("Generating: High Risk Matrix...")
    
    # Scatter plot of Default Rate vs Avg Delay
    plt.figure()
    sns.scatterplot(data=exporters, x='avg_payment_delay', y='default_rate', 
                    size='total_invoices', hue='industry', sizes=(20, 200), alpha=0.7)
    
    plt.title('Exporter Risk Matrix: Default Rate vs. Avg Delay')
    plt.xlabel('Average Payment Delay (Days)')
    plt.ylabel('Default Rate (0-1)')
    plt.axvline(30, color='red', linestyle='--', alpha=0.5, label='High Delay Threshold (30d)')
    plt.axhline(0.10, color='red', linestyle='--', alpha=0.5, label='High Default Threshold (10%)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'exporter_risk_matrix.png'))
    plt.close()

    # Generate Top Ridks Table
    high_risk = exporters[exporters['default_rate'] > 0.10].sort_values('default_rate', ascending=False)
    high_risk_table = high_risk[['exporter_id', 'industry', 'country', 'total_invoices', 'default_rate', 'avg_payment_delay']]
    
    csv_path = os.path.join(output_dir, 'high_risk_exporters.csv')
    high_risk_table.to_csv(csv_path, index=False)
    print(f"High risk exporters list saved to {csv_path}")

    return high_risk_table

def main():
    try:
        invoices, exporters = load_data()
        
        merged_df = plot_delay_by_country_industry(invoices, exporters, OUTPUT_REPORT_DIR)
        analyze_amount_vs_delay(invoices, OUTPUT_REPORT_DIR)
        risk_table = identify_high_risk_exporters(exporters, OUTPUT_REPORT_DIR)
        
        # Printed Summary for the User
        print("\n--- EDA Summary Insights ---")
        
        print(f"1. Overall Avg Payment Delay: {invoices['payment_delay_days'].mean():.2f} days")
        
        print("\n2. Delay by Industry (Top 3 Highest):")
        print(merged_df.groupby('industry')['payment_delay_days'].mean().sort_values(ascending=False).head(3))
        
        print("\n3. Delay by Importer Country (Top 3 Slowest):")
        print(merged_df.groupby('importer_country')['payment_delay_days'].mean().sort_values(ascending=False).head(3))
        
        print("\n4. High Risk Exporter Count:")
        print(f"   Found {len(risk_table)} exporters with Default Rate > 10%")
        
        print(f"\nCharts saved to: {os.path.abspath(OUTPUT_REPORT_DIR)}")

    except FileNotFoundError:
        print("Error: Processed data not found. Please run etl_pipeline.py first.")

if __name__ == "__main__":
    main()
