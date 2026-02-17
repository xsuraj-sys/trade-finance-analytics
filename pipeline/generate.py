
import csv
import random
import datetime
import os

# Configuration
NUM_EXPORTERS = 50
NUM_INVOICES = 1000
START_DATE = datetime.date(2023, 1, 1)
END_DATE = datetime.date.today()

# Sample Data
INDUSTRIES = ['Textiles', 'Electronics', 'Agriculture', 'Machinery', 'Pharmaceuticals', 'Autos']
EXPORTER_COUNTRIES = ['India', 'China', 'Vietnam', 'Bangladesh', 'Turkey', 'Mexico']
IMPORTER_COUNTRIES = ['USA', 'Germany', 'UK', 'UAE', 'Singapore', 'Canada', 'France']
STATUSES_PAID = ['Paid', 'Paid Late']
STATUSES_OPEN = ['Outstanding', 'Overdue']
STATUSES_DEFAULT = ['Defaulted', 'Written-off']

# Helper Functions
def random_date(start, end):
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def generate_exporters(n=NUM_EXPORTERS):
    exporters = []
    for i in range(1, n + 1):
        exporter_id = f"EXP_{i:03d}"
        company_age = random.randint(1, 50)
        industry = random.choice(INDUSTRIES)
        country = random.choice(EXPORTER_COUNTRIES)
        # We will calculate total and defaulted invoices later after generating invoices,
        # but for now let's generate realistic base stats or leave placeholders
        total_invoices = 0
        defaulted_invoices = 0
        
        exporters.append({
            "exporter_id": exporter_id,
            "company_age": company_age,
            "industry": industry,
            "country": country,
            "total_invoices": total_invoices,
            "defaulted_invoices": defaulted_invoices
        })
    return exporters

def generate_invoices_and_transactions(exporters, n=NUM_INVOICES):
    invoices = []
    transactions = []
    exporter_stats = {e['exporter_id']: {'total': 0, 'defaulted': 0} for e in exporters}

    for i in range(1, n + 1):
        invoice_id = f"INV_{i:04d}"
        exporter = random.choice(exporters)
        exporter_id = exporter['exporter_id']
        importer_country = random.choice(IMPORTER_COUNTRIES)
        
        # Determine Amount
        invoice_amount = round(random.uniform(5000, 150000), 2)
        
        # Dates
        invoice_date = random_date(START_DATE, END_DATE)
        term_days = random.choice([30, 45, 60, 90])
        due_date = invoice_date + datetime.timedelta(days=term_days)
        
        # Decide Outcome based on exporter 'risk' (simulated randomness)
        rand_outcome = random.random()
        
        status = ""
        payment_date = None
        payment_amount = 0.0
        payment_delay_days = 0
        
        # 70% Paid on time or slightly late (0-5 days late deemed acceptable)
        if rand_outcome < 0.70:
            delay = random.randint(-5, 5)
            payment_date = due_date + datetime.timedelta(days=delay)
            status = 'Paid'
            payment_amount = invoice_amount
            payment_delay_days = delay
            
        # 20% Paid Late (6-60 days late)
        elif rand_outcome < 0.90:
            delay = random.randint(6, 60)
            payment_date = due_date + datetime.timedelta(days=delay)
            status = 'Paid Late'
            payment_amount = invoice_amount
            payment_delay_days = delay
            
        # 5% Defaulted
        elif rand_outcome < 0.95:
            delay = random.randint(90, 180) # Significant delay before default recognized usually
            # Often no payment date if defaulted, but let's say partial recovery or just track delay
            payment_date = None 
            status = 'Defaulted'
            payment_amount = round(invoice_amount * random.uniform(0, 0.4), 2) # Partial recovery
            payment_delay_days = (datetime.date.today() - due_date).days if due_date < datetime.date.today() else 0
            exporter_stats[exporter_id]['defaulted'] += 1
            
        # 5% Outstanding (Current / Not due yet or just late but not resolved)
        else:
            if due_date > datetime.date.today():
                status = 'Outstanding'
                delay = 0
            else:
                status = 'Overdue'
                delay = (datetime.date.today() - due_date).days
            payment_date = None
            payment_amount = 0.0
            payment_delay_days = delay

        exporter_stats[exporter_id]['total'] += 1

        invoices.append({
            "invoice_id": invoice_id,
            "exporter_id": exporter_id,
            "importer_country": importer_country,
            "invoice_amount": invoice_amount,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "payment_date": payment_date if payment_date else "",
            "status": status
        })
        
        # Creating a transaction only if a payment was made (full or partial)
        if payment_amount > 0:
            transactions.append({
                "transaction_id": f"TXN_{i:04d}",
                "invoice_id": invoice_id,
                "payment_amount": payment_amount,
                "payment_delay_days": payment_delay_days
            })

    # Update exporter stats
    for exporter in exporters:
        stats = exporter_stats[exporter['exporter_id']]
        exporter['total_invoices'] = stats['total']
        exporter['defaulted_invoices'] = stats['defaulted']

    return invoices, transactions

def write_csv(filename, data, fieldnames):
    filepath = os.path.join('data', filename)
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated {filepath} with {len(data)} records.")

# Main Execution
exporters = generate_exporters()
invoices, transactions = generate_invoices_and_transactions(exporters)

write_csv('exporters.csv', exporters, ['exporter_id', 'company_age', 'industry', 'country', 'total_invoices', 'defaulted_invoices'])
write_csv('invoices.csv', invoices, ['invoice_id', 'exporter_id', 'importer_country', 'invoice_amount', 'invoice_date', 'due_date', 'payment_date', 'status'])
write_csv('transactions.csv', transactions, ['transaction_id', 'invoice_id', 'payment_amount', 'payment_delay_days'])
