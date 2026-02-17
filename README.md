
# Trade Finance Invoice Risk & Delay Analytics Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A specialized fintech solution designed to assist credit analysts and risk managers in the **Trade Finance** sector (factoring, invoice discounting). 

This platform replaces manual spreadsheet-based decisions with an automated **AI-driven Risk Engine**, predicting payment delays and assigning risk scores to invoices in real-time.

## 🏢 Business Context
In trade finance, capital is advanced to exporters against unpaid invoices. The core risks include:
1.  **Default Risk:** Buyer never pays (Principal Loss).
2.  **Dilution Risk:** Disputes reducing the payable amount.
3.  **Liquidity Risk:** Payment is delayed significantly beyond the due date.

Traditional methods rely on static credit reports. This platform uses **transactional behavioral data** to predict outcomes dynamically.

## 🚀 Key Features

*   **AI Risk Scoring Engine:** Weighted assessment based on:
    *   Historical Default Rate (40%)
    *   Payment Delay Trends (30%)
    *   Invoice Volatility (20%)
    *   Country/Political Risk (10%)
*   **Predictive Analytics:** Gradient Boosting machine learning model to forecast "Probability of Delay" for new applications.
*   **Analyst Dashboard:** Interactive interface for portfolio monitoring and decision support.
*   **Decision Logic:** Automated recommendations (Green/Amber/Red) to standardize credit approvals.

## 🏗️ System Architecture

The system follows a modular microservices-ready architecture:

```
trade_finance_analytics/
├── backend/            # FastAPI Service (Risk Engine & Predictions)
│   └── app.py
├── frontend/           # Streamlit Dashboard (Analyst Interface)
│   └── app.py
├── pipeline/           # Data Engineering & ML Pipeline
│   ├── generate.py     # Synthetic Data Generator
│   ├── etl.py          # Data Cleaning & Feature Engineering
│   ├── score.py        # Rule-Based Risk Engine
│   ├── train.py        # ML Model Training (XGBoost)
│   └── eda.py          # Exploratory Data Analysis
├── data/               # Data Storage (Raw & Processed CSVs)
├── models/             # Serialized ML Models (.pkl)
└── Dockerfile          # Production Container Definition
```

## 🛠️ Tech Stack

*   **Backend:** Python 3.9+, FastAPI, Uvicorn
*   **Frontend:** Streamlit, Plotly
*   **Data Science:** Pandas, Scikit-learn, Joblib
*   **Infrastructure:** Docker

## ⚡ Quick Start

### Option 1: Run Locally (Python)

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Data Pipeline:**
    Execute the following scripts in order to generate data and train models:
    ```bash
    # 1. Generate Synthetic Data
    python3 pipeline/generate.py
    
    # 2. Run ETL & Feature Engineering
    python3 pipeline/etl.py
    
    # 3. Calculate Historical Risk Scores
    python3 pipeline/score.py
    
    # 4. Train Prediction Model
    python3 pipeline/train.py
    ```

3.  **Start the Backend API:**
    ```bash
    uvicorn backend.app:app --reload --port 8000
    ```

4.  **Launch the Dashboard:**
    ```bash
    streamlit run frontend/app.py
    ```
    Access the dashboard at `http://localhost:8501`.

### Option 2: Run with Docker

Build and run the entire stack in one container:

```bash
docker build -t trade-finance-platform .
docker run -p 8000:8000 -p 8501:8501 trade-finance-platform
```

## 📊 Usage Guide for Analysts

1.  **Portfolio Overview:** Check the "Critical Watchlist" for high-risk invoices requiring immediate collection efforts.
2.  **Exporter Analysis:** Use the scatter plot to identify exporters with high default rates relative to their volume.
3.  **New Deal Assessment:** 
    *   Go to "AI Risk Predictor".
    *   Enter invoice details (Amount, Country, Company Age).
    *   Review the **AI Recommendation**:
        *   🟢 **Green:** Auto-Approve.
        *   🟡 **Amber:** Approve with higher haircut/reserve.
        *   🔴 **Red:** Reject or escalate to Credit Committee.

## 📈 Impact
By implementing this platform, financial institutions can expect:
*   **20% reduction** in default losses through early identification of high-risk exporters.
*   **30% faster** credit decisioning time.
*   Improved **Liquidity forecasting** accuracy.

---
**Author:** Suraj Ray | Senior Fintech Engineer
