# component-d/argument_mapping/train_scspm.py
"""
XGBoost Training Script for Citation Strength Prediction Model (SCSPM).

PURPOSE:
Reads the generated training_data.csv and trains an XGBoost Regressor to 
predict the citation strength score (0-100) of a legal precedent.

WHY XGBoost?
XGBoost is a highly efficient, gradient-boosting framework. It excels at 
handling tabular data and capturing non-linear relationships between legal 
features (like Court Level, Recency, and Citation Density) without requiring 
massive amounts of data.
"""

import os
import pandas as pd
import xgboost as xgb
from joblib import dump
from sklearn.model_selection import train_test_split

def main():
    print("Starting SCSPM Model Training...")
    
    # 1. LOAD THE DATASET
    csv_path = os.path.join(os.path.dirname(__file__), "..", "training_data.csv")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Please run generate_training_data.py first.")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} cases for training.")

    # 2. PREPARE FEATURES (X) AND TARGET (y)
    # We drop 'doc_id' because it's just a label, not a mathematical feature.
    features = ['court_level', 'recency_score', 'validity_score', 'outgoing_citations', 'incoming_citation_density']
    target = 'target_strength_score'

    X = df[features]
    y = df[target]

    # 3. INITIALIZE THE XGBoost MODEL
    # Note: Since we only have 30 cases, we use shallow trees (max_depth=2) 
    # and fewer estimators (n_estimators=50) to prevent overfitting.
    model = xgb.XGBRegressor(
        n_estimators=50, 
        learning_rate=0.1, 
        max_depth=2, 
        objective='reg:squarederror',
        random_state=42
    )

    # 4. TRAIN THE MODEL
    print("Training XGBoost Regressor...")
    model.fit(X, y)

    # 5. SAVE THE TRAINED MODEL
    # We save it as a .pkl file so the FastAPI endpoint can load it instantly later.
    model_path = os.path.join(os.path.dirname(__file__), "scspm_model.pkl")
    dump(model, model_path)
    print(f"SUCCESS! Model saved to {model_path}")

    # 6. QUICK TEST PREDICTION (To prove it works)
    # Let's predict the strength of a hypothetical "Heavy" Supreme Court case
    test_case = pd.DataFrame([{
        'court_level': 3,             # Supreme Court
        'recency_score': 3,           # Very recent
        'validity_score': 3,          # Good law
        'outgoing_citations': 50,     # Cites 50 cases (Heavy precedent)
        'incoming_citation_density': 30 # High density
    }])
    
    prediction = model.predict(test_case)[0]
    print(f"\n--- MODEL TEST ---")
    print(f"Predicted strength for a heavy SC case: {prediction:.2f}%")
    print(f"------------------\n")

if __name__ == "__main__":
    main()