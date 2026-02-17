
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
from pydantic import BaseModel
from typing import Optional, List, Dict

# Configuration
INPUT_DIR = 'processed_data'
MODEL_DIR = 'models'

app = FastAPI(
    title="Trade Finance Analytics API",
    description="API for invoice risk scoring, exporter profiling, and payment delay prediction.",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Data/Model on Startup
invoices_scored = None
exporters_scored = None
delay_model = None

@app.on_event("startup")
async def load_resources():
    global invoices_scored, exporters_scored, delay_model
    
    # Load Processed Data (In-Memory Database for Demo)
    try:
        invoices_scored = pd.read_csv(os.path.join(INPUT_DIR, 'invoices_scored.csv'))
        invoices_scored['invoice_id'] = invoices_scored['invoice_id'].astype(str)
        print("Loaded invoices data.")
    except Exception as e:
        print(f"Warning: Could not load invoices data. {e}")
        invoices_scored = pd.DataFrame()

    try:
        exporters_scored = pd.read_csv(os.path.join(INPUT_DIR, 'exporters_scored.csv'))
        exporters_scored['exporter_id'] = exporters_scored['exporter_id'].astype(str)
        print("Loaded exporters data.")
    except Exception as e:
        print(f"Warning: Could not load exporters data. {e}")
        exporters_scored = pd.DataFrame()

    # Load Model
    try:
        model_path = os.path.join(MODEL_DIR, 'delay_prediction_model.pkl')
        delay_model = joblib.load(model_path)
        print("Loaded delay prediction model.")
    except Exception as e:
        print(f"Warning: Could not load model. {e}")
        delay_model = None

# --- Logic ---

def get_recommendation(prob: float) -> Dict[str, str]:
    """
    Business Logic for Risk Decisioning
    """
    if prob > 0.7:
        return {
            "action": "Reject / Manual Review",
            "details": "High likelihood of default/delay (>70%). Financing this invoice poses significant capital risk.",
            "impact": "Potential Loss of Principal",
            "code": "RED"
        }
    elif prob >= 0.4:
        return {
            "action": "Approve with Safeguards",
            "details": "Moderate risk. Recommend lower advance rate (e.g., 80% instead of 90%) or requiring recourse.",
            "impact": "Liquidity Drag",
            "code": "AMBER"
        }
    else:
        return {
            "action": "Auto Approve",
            "details": "Low risk profile. Standard financing terms apply.",
            "impact": "Standard Yield",
            "code": "GREEN"
        }

# --- Pydantic Models ---

class ExporterResponse(BaseModel):
    exporter_id: str
    company_age: int
    industry: str
    country: str
    total_invoices: int
    default_rate: float
    avg_payment_delay: float

class InvoiceRiskResponse(BaseModel):
    invoice_id: str
    exporter_id: str
    importer_country: str
    invoice_amount: float
    risk_score: float
    risk_category: str
    risk_explanation: str
    predicted_delay_prob: Optional[float] = None
    recommendation: Optional[Dict[str, str]] = None

class PredictionRequest(BaseModel):
    invoice_amount: float
    risk_score: float
    company_age: int
    importer_country: str
    industry: str
    exporter_country: str

class PredictionResponse(BaseModel):
    probability_of_delay: float
    is_high_risk: bool
    input_summary: dict
    recommendation: Dict[str, str]

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Trade Finance Analytics API is running", "status": "ok"}

@app.get("/api/v1/invoices/{invoice_id}", response_model=InvoiceRiskResponse)
def get_invoice_risk(invoice_id: str):
    """
    Get the pre-calculated risk score and details for a specific historical invoice.
    """
    if invoices_scored.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    invoice = invoices_scored[invoices_scored['invoice_id'] == invoice_id]
    if invoice.empty:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    row = invoice.iloc[0]
    
    # Estimate probability from risk_score (0-100) for recommendation purposes
    # Logic: Risk Score 100 -> Prob 1.0 approx
    est_prob = row['risk_score'] / 100.0
    rec = get_recommendation(est_prob)
    
    return {
        "invoice_id": row['invoice_id'],
        "exporter_id": row['exporter_id'],
        "importer_country": row['importer_country'],
        "invoice_amount": row['invoice_amount'],
        "risk_score": row['risk_score'],
        "risk_category": row['risk_category'],
        "risk_explanation": row['risk_explanation'],
        "recommendation": rec
    }

@app.get("/api/v1/exporters/{exporter_id}", response_model=ExporterResponse)
def get_exporter_metrics(exporter_id: str):
    """
    Get reliability metrics for a financing applicant (exporter).
    """
    if exporters_scored.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    exporter = exporters_scored[exporters_scored['exporter_id'] == exporter_id]
    if exporter.empty:
        raise HTTPException(status_code=404, detail="Exporter not found")
    
    row = exporter.iloc[0]
    return {
        "exporter_id": row['exporter_id'],
        "company_age": int(row['company_age']),
        "industry": row['industry'],
        "country": row['country'],
        "total_invoices": int(row['total_invoices']),
        "default_rate": float(row['default_rate']), 
        "avg_payment_delay": float(row['avg_payment_delay'])
    }

@app.post("/api/v1/predict/delay", response_model=PredictionResponse)
def predict_invoice_delay(request: PredictionRequest):
    """
    Use the ML model to predict the probability of delay for a NEW invoice application.
    """
    if delay_model is None:
        raise HTTPException(status_code=503, detail="ML Model not loaded")

    # Prepare DataFrame for Model
    input_data = pd.DataFrame([{
        'invoice_amount': request.invoice_amount,
        'risk_score': request.risk_score,
        'company_age': request.company_age,
        'importer_country': request.importer_country,
        'industry': request.industry,
        'country': request.exporter_country
    }])
    
    try:
        # Predict Probability of Class 1 (Delayed)
        prob = delay_model.predict_proba(input_data)[0][1]
        
        return {
            "probability_of_delay": round(prob, 4),
            "is_high_risk": prob > 0.5,
            "input_summary": request.dict(),
            "recommendation": get_recommendation(prob)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/api/v1/invoices", response_model=List[InvoiceRiskResponse])
def list_invoices(limit: int = 10):
    if invoices_scored.empty:
        return []
    
    subset = invoices_scored.head(limit)
    response = []
    for _, row in subset.iterrows():
        est_prob = row['risk_score'] / 100.0
        response.append({
            "invoice_id": row['invoice_id'],
            "exporter_id": row['exporter_id'],
            "importer_country": row['importer_country'],
            "invoice_amount": row['invoice_amount'],
            "risk_score": row['risk_score'],
            "risk_category": row['risk_category'],
            "risk_explanation": row['risk_explanation'],
            "recommendation": get_recommendation(est_prob)
        })
    return response
