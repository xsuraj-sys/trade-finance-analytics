
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Configuration
INPUT_DIR = 'processed_data'
MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

def load_dataset():
    # Load all necessary files
    invoices_scored = pd.read_csv(os.path.join(INPUT_DIR, 'invoices_scored.csv'))
    invoices_enriched = pd.read_csv(os.path.join(INPUT_DIR, 'invoices_enriched.csv'))
    exporters = pd.read_csv(os.path.join(INPUT_DIR, 'exporters_scored.csv'))
    
    # We need:
    # 1. Target: 'is_delayed' (from invoices_enriched)
    # 2. Features: 'invoice_amount' (in both), 'risk_score' (in scored), 
    #              'company_age' (in exporters), 'importer_country' (in invoices), 'industry' (in exporters)
    
    # Join target back to scored
    df = pd.merge(invoices_scored, invoices_enriched[['invoice_id', 'is_delayed']], on='invoice_id', how='left')
    
    # Join exporter details
    df = pd.merge(df, exporters[['exporter_id', 'company_age', 'industry', 'country']], 
                  on='exporter_id', how='left', suffixes=('', '_exporter'))
    
    # Clean up
    # Target to int
    df['target'] = df['is_delayed'].astype(int)
    
    print(f"Dataset loaded: {df.shape[0]} samples")
    return df

def train_model(df):
    print("Preparing training data...")
    
    # Feature Selection
    # Numerical Features
    num_features = ['invoice_amount', 'risk_score', 'company_age']
    # Categorical Features
    cat_features = ['importer_country', 'industry', 'country'] # 'country' is exporter country
    
    X = df[num_features + cat_features]
    y = df['target']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Pipeline: Preprocessing + Model
    # We use GradientBoostingClassifier (similar to XGBoost)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
        ])
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42))
    ])
    
    # Train
    print("Training Gradient Boosting Model...")
    pipeline.fit(X_train, y_train)
    
    # Predict
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    # Evaluate
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save
    model_path = os.path.join(MODEL_DIR, 'delay_prediction_model.pkl')
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")
    
    return pipeline, X_test, y_test

def predict_sample(model, df):
    print("\n--- Sample Predictions (Test Set) ---")
    # Take 5 random samples
    sample = df.sample(5)
    
    # Predict
    probs = model.predict_proba(sample)[:, 1]
    results = sample.copy()
    results['predicted_delay_prob'] = probs
    
    columns_to_show = ['invoice_id', 'importer_country', 'invoice_amount', 'risk_score', 'target', 'predicted_delay_prob']
    print(results[columns_to_show])

if __name__ == "__main__":
    df = load_dataset()
    if not df.empty:
        model, X_test_raw, y_test = train_model(df)
        
        # We pass the original DF subset corresponding to X_test to show readable cols
        # Getting the original rows for the test set
        test_indices = X_test_raw.index
        df_test = df.loc[test_indices]
        
        predict_sample(model, df_test)
