# component-d/argument_mapping/explain_citation.py
"""
SHAP Explainability Script for Citation Strength Prediction.

PURPOSE:
Lawyers do not trust "black box" AI. If the UI shows a Citation Strength 
of 89%, the lawyer needs to know WHY. This script uses the SHAP library 
to analyze the XGBoost model and generate human-readable explanations 
for the predicted score.

HOW IT WORKS:
SHAP (SHapley Additive exPlanations) calculates the exact contribution 
of each feature (Court Level, Recency, etc.) to the final prediction.
"""

import os
import joblib
import pandas as pd
import shap
import numpy as np

# Path to the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "scspm_model.pkl")

def load_model():
    """Loads the trained XGBoost model from the .pkl file."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("scspm_model.pkl not found. Please run train_scspm.py first.")
    return joblib.load(MODEL_PATH)

def generate_explanation(features_dict):
    """
    Takes a dictionary of case features, predicts the score, 
    and returns a human-readable explanation of the score.
    """
    model = load_model()
    
    # Convert dictionary to DataFrame for XGBoost
    df = pd.DataFrame([features_dict])
    
    # 1. Get the raw prediction
    prediction = model.predict(df)[0]
    
    # 2. Initialize SHAP TreeExplainer (optimized for XGBoost)
    explainer = shap.TreeExplainer(model)
    
    # 3. Calculate SHAP values (the impact of each feature)
    shap_values = explainer.shap_values(df)
    
    # 4. Calculate the base value (the average score of all training cases)
    base_value = explainer.expected_value
    
    # 5. Build the explanation text
    explanation_parts = []
    
    # Map feature names to readable labels for the UI
    feature_labels = {
        'court_level': 'Court Level',
        'recency_score': 'Case Recency',
        'validity_score': 'Validity Status',
        'outgoing_citations': 'Citation Complexity',
        'incoming_citation_density': 'Citation Density'
    }
    
    # Iterate through features and their SHAP values
    for i, feature in enumerate(df.columns):
        impact = shap_values[0][i]
        label = feature_labels.get(feature, feature)
        
        # Format the impact (e.g., "+12.5%" or "-5.2%")
        if impact > 0.5:
            explanation_parts.append(f"{label} added +{impact:.1f}% to the score.")
        elif impact < -0.5:
            explanation_parts.append(f"{label} reduced the score by {abs(impact):.1f}%.")
            
    # Combine into a final reasoning string
    reasoning = " ".join(explanation_parts)
    
    return {
        "predicted_score": round(float(prediction), 1),
        "base_score": round(float(base_value), 1),
        "reasoning": reasoning,
        "feature_impacts": {feature_labels[f]: round(float(shap_values[0][i]), 2) for i, f in enumerate(df.columns)}
    }

if __name__ == "__main__":
    print("--- Testing SHAP Explainability ---")
    
    # Test Case 1: A heavy, recent Supreme Court case
    heavy_case = {
        'court_level': 3,             # Supreme Court
        'recency_score': 3,           # Very recent
        'validity_score': 3,          # Good law
        'outgoing_citations': 50,     # Cites 50 cases
        'incoming_citation_density': 30 # High density
    }
    
    result = generate_explanation(heavy_case)
    print(f"\nPredicted Score: {result['predicted_score']}%")
    print(f"Reasoning: {result['reasoning']}")
    
    print("\n--- Feature Impacts ---")
    for feature, impact in result['feature_impacts'].items():
        print(f"{feature}: {impact:+.2f}")
        
    print("\n---------------------------------")