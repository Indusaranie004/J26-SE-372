# component-d/argument_mapping/generate_training_data.py
"""
Data Extraction Script for Function 2: Citation Strength Prediction (SCSPM).

PURPOSE:
This script reads the ingested Supreme Court judgment JSON files provided 
by Component A. It extracts key legal metadata and converts them into 
numerical features to train the XGBoost model.

HOW IT WORKS (The AI vs. UI Pipeline):
1. This script generates NUMBERS (e.g., Citation Density = 15) for the CSV.
2. XGBoost uses these NUMBERS to calculate the final strength score (e.g., 89%).
3. Later, when sending data to the UI, we translate these NUMBERS back into 
   WORDS (e.g., 15 -> "Medium") so the lawyer can understand them easily.
"""

import os
import json
import csv
import glob
import random
from datetime import datetime

# Path to Component A's ingested case data
COMPONENT_A_CASES_DIR = "../component-a/corpus/cases"

# ==============================================================================
# 1. FEATURE EXTRACTION FUNCTIONS (Converting Text to Numbers for AI)
# ==============================================================================

def get_court_score(court):
    """
    Converts court hierarchy to a number. 
    Higher courts have more precedential weight.
    SC (Supreme Court) = 3, CA (Court of Appeal) = 2, HC (High Court) = 1.
    """
    if not court: return 1
    court = court.upper()
    if "SC" in court: return 3
    if "CA" in court or "APPEAL" in court: return 2
    return 1

def get_recency_score(date_str):
    """
    Calculates recency based on judgment date.
    Newer cases are generally more relevant. 
    <= 5 yrs = 3 (High), 6-10 yrs = 2 (Medium), > 10 yrs = 1 (Low).
    """
    try:
        case_date = datetime.strptime(date_str, "%Y-%m-%d")
        age_years = (datetime.now() - case_date).days / 365.25
        
        if age_years <= 5: return 3  
        elif age_years <= 10: return 2 
        else: return 1 
    except ValueError:
        return 1

def get_validity_score(status):
    """
    Converts validity status to a number.
    A case that is 'good_law' is highly citable. Overruled cases have 0 strength.
    """
    if status == "good_law": return 3
    if status == "partially_invalidated": return 1
    return 0 

# ==============================================================================
# 2. UI TRANSLATION FUNCTIONS (Converting Numbers back to Words for the UI)
# ==============================================================================

def get_citation_density_label(incoming_count):
    """
    Translates the raw citation count number into the label shown on the UI.
    This is NOT done by SHAP. This is a simple display rule for the frontend.
    """
    if incoming_count >= 20:
        return "High"
    elif incoming_count >= 10:
        return "Medium"
    else:
        return "Low"

# ==============================================================================
# 3. MAIN EXECUTION (Generating the CSV)
# ==============================================================================

def main():
    print(f"Scanning Component A cases in: {os.path.abspath(COMPONENT_A_CASES_DIR)}")
    json_files = glob.glob(f"{COMPONENT_A_CASES_DIR}/*.json")
    
    if not json_files:
        print("ERROR: No JSON files found. Check the COMPONENT_A_CASES_DIR path.")
        return

    csv_path = "training_data.csv"
    
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write the header row. These are the features (X) and the target (y) for XGBoost.
        writer.writerow([
            "doc_id",                       # Unique identifier for the case
            "court_level",                  # Feature 1: Court hierarchy score (1-3)
            "recency_score",                # Feature 2: Age of the case (1-3)
            "validity_score",               # Feature 3: Current legal validity (0-3)
            "incoming_citation_density",    # Feature 4: How many times THIS case is cited
            "target_strength_score"         # Target (y): The predicted citation strength (0-100)
        ])

        for path in json_files:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Extract raw metadata from Component A's JSON structure
                doc_id = data.get("doc_id", "unknown")
                court = data.get("court", "SC")
                date = data.get("date", "2010-01-01")
                validity = data.get("validity_status", "good_law")
                
                # Convert raw metadata into numerical ML features
                # --- CRITICAL: Count actual citations in this specific JSON ---
                entities = data.get("entities", {})
                citations_list = entities.get("citations", [])
                outgoing_citations = len(citations_list) 

                court_score = get_court_score(court)
                recency_score = get_recency_score(date)
                validity_score = get_validity_score(validity)
                
                # --- CALCULATE INCOMING CITATION DENSITY ---
                # Note: In the LIVE API, this will be a real Neo4j query counting TREATED_BY edges.
                # For the training CSV, we simulate it heuristically based on Court Level and Age.
                try:
                    case_date = datetime.strptime(date, "%Y-%m-%d")
                    age_years = (datetime.now() - case_date).days / 365.25
                except:
                    age_years = 10
                
                # Heuristic: Older SC cases naturally accumulate more incoming citations.
                incoming_citation_density = (court_score * 3) + max(0, int(10 - (age_years / 2)))
                
                # Base density (older SC cases get cited more) + Complexity bonus (citing many cases means it's a heavy precedent)
                base_density = (court_score * 3) + max(0, int(10 - (age_years / 2)))
                complexity_bonus = outgoing_citations * 0.4 # 0.4 multiplier ensures a nice spread
                random_variance = random.uniform(-2, 2) 

                incoming_citation_density = max(0, int(base_density + complexity_bonus + random_variance))
                
                # --- TARGET SCORE CALCULATION (0-100) ---
                # Base 40 + Court(15) + Recency(15) + Validity(15) + Citation Density(15 max)
                target_score = 40 + (court_score * 5) + (recency_score * 5) + (validity_score * 5) + (incoming_citation_density * 0.4)
                
                # Add slight random variance to the final score
                target_score = target_score + random.uniform(-3, 3)
                target_score = min(100, max(0, int(target_score))) 
                
                # Write the row to the CSV
                writer.writerow([
                    doc_id, court_score, recency_score, validity_score, 
                    incoming_citation_density, target_score
                ])
                
                # OPTIONAL: Print a sample to show how the translation works
                if doc_id == json_files[0].split("\\")[-1].replace(".json", ""):
                    print(f"\n--- EXAMPLE TRANSLATION FOR UI ---")
                    print(f"Case: {doc_id}")
                    print(f"Raw Number for AI: {incoming_citation_density}")
                    print(f"Label shown on UI: {get_citation_density_label(incoming_citation_density)}")
                    print(f"----------------------------------\n")
                
    print(f"\nSUCCESS! Generated '{csv_path}' with {len(json_files)} rows.")
    print("This dataset is now ready to train the XGBoost SCSPM model.")

if __name__ == "__main__":
    main()