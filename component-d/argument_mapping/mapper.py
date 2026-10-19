# component-d/argument_mapping/mapper.py
"""
Dynamic Argument Map Builder for Function 2.

PURPOSE:
1. Uses LLM to dynamically generate the logical structure of arguments.
2. Queries Component A's API to find real cases matching the arguments.
3. Calculates real-time XGBoost citation strength scores for found cases.
"""

import os
import json
import requests
import joblib
import pandas as pd
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# Import local modules
from .argument_prompts import build_argument_messages
from .explain_citation import generate_explanation

load_dotenv()

# --- CONFIGURATION ---
COMPONENT_A_API = os.getenv("COMPONENT_A_API", "http://127.0.0.1:8001")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "scspm_model.pkl")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def load_model():
    """Loads the trained XGBoost model from the .pkl file."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def call_llm_for_structure(issue_question: str) -> dict:
    """Calls Groq to dynamically generate the argument map logic."""
    client = Groq(api_key=GROQ_API_KEY)
    messages = build_argument_messages(issue_question)
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b", # Or your preferred model
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[ERROR] LLM Generation Failed: {e}")
        # Fallback if LLM fails
        return {"supporting_arguments": [], "opposing_arguments": [], "conclusion": "Error generating map."}

def search_real_authorities(legal_text: str) -> list:
    """
    Searches Component A's database for real cases matching the legal argument.
    Returns a list of real doc_ids found in the corpus.
    """
    try:
        # Component A's /search endpoint accepts a POST request with query and top_k
        response = requests.post(
            f"{COMPONENT_A_API}/search", 
            json={"query": legal_text, "mode": "hybrid", "top_k": 2}, 
            timeout=5
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            # Extract only the doc_ids of real cases found in the corpus
            return [r["doc_id"] for r in results if "doc_id" in r]
    except Exception as e:
        print(f"[WARNING] Component A Search Error: {e}")
    return []

def get_real_time_score(doc_id: str) -> dict:
    """Fetches features from Component A and predicts score using XGBoost."""
    try:
        # 1. Get Case Metadata
        case_res = requests.get(f"{COMPONENT_A_API}/cases/{doc_id}", timeout=3)
        case_data = case_res.json() if case_res.status_code == 200 else {}
        
        # 2. Get Incoming Citations (TREATED_BY edges)
        cit_res = requests.get(f"{COMPONENT_A_API}/cases/{doc_id}/citations", timeout=3)
        citations = cit_res.json().get("citations", []) if cit_res.status_code == 200 else []
        
        # 3. Extract Features
        court = case_data.get("court", "SC").upper()
        court_level = 3 if "SC" in court else (2 if "CA" in court else 1)
        
        try:
            age = (datetime.now() - datetime.strptime(case_data.get("date", "2010-01-01"), "%Y-%m-%d")).days / 365.25
            recency_score = 3 if age <= 5 else (2 if age <= 10 else 1)
        except: recency_score = 1
        
        validity = case_data.get("validity_status", "good_law")
        validity_score = 3 if validity == "good_law" else (1 if validity == "partially_invalidated" else 0)
        
        outgoing = len(case_data.get("entities", {}).get("citations", []))
        incoming = len(citations)
        
        features = {
            "court_level": court_level, "recency_score": recency_score,
            "validity_score": validity_score, "outgoing_citations": outgoing,
            "incoming_citation_density": incoming
        }
        
        # 4. Predict using the trained XGBoost model
        model = load_model()
        if model:
            df = pd.DataFrame([features])
            score = float(model.predict(df)[0])
            explanation = generate_explanation(features)
            return {
                "doc_id": doc_id,
                "name": case_data.get("case_num", doc_id), # Use real case number as the display name
                "score": round(score, 1), 
                "reasoning": explanation["reasoning"], 
                "status": validity
             }
     
    except Exception as e:
        print(f"[WARNING] ML Prediction Error for {doc_id}: {e}")
    return None
        
def build_argument_map(issue_id: str, issue_question: str) -> dict:
    """Main orchestration function: combines LLM generation and ML enrichment."""
    
    # 1. Get logical structure from LLM
    llm_structure = call_llm_for_structure(issue_question)
    
    # 2. Helper function to process arguments and attach real ML scores
    def process_arguments(args_list, stance):
        processed = []
        for i, arg in enumerate(args_list):
            authorities = []

            # Search Component A for real cases matching this argument's legal text
            real_doc_ids = search_real_authorities(arg["text"])
                            
            # Calculate real XGBoost scores for each found case
            for doc_id in real_doc_ids:
                ml_data = get_real_time_score(doc_id)
                if ml_data:
                    authorities.append({
                        "id": f"auth_{stance}_{i}_{doc_id}",
                        "name": ml_data["name"],
                        "doc_id": ml_data["doc_id"],
                        "score": ml_data["score"],
                        "relationship": "Supports" if stance == "supporting" else "Opposing",
                        "type": "Judicial decision",
                        "status": ml_data["status"],
                        "shap_reasoning": ml_data["reasoning"] # The explainability text for the UI
                    })
            
            processed.append({
                "id": f"arg_{stance}_{i}",
                "text": arg["text"],
                "stance": stance,
                "evidence": [{"id": f"ev_{stance}_{i}_{j}", "text": ev, "status": "needed"} for j, ev in enumerate(arg.get("evidence", []))],
                "authorities": authorities
            })
        return processed

    # Process both sides of the argument
    supporting = process_arguments(llm_structure.get("supporting_arguments", []), "supporting")
    opposing = process_arguments(llm_structure.get("opposing_arguments", []), "opposing")

    # 3. Return final JSON for UI
    return {
        "issue_id": issue_id,
        "issue_question": issue_question,
        "conclusion": llm_structure.get("conclusion", "Analysis pending."),
        "conclusion_stance": llm_structure.get("conclusion_stance", "Contested"),
        "supporting_arguments": supporting,
        "opposing_arguments": opposing,
        "strength_analysis": {
            "overall_strength": 70, # Can be calculated dynamically later
            "evidence_gaps": sum(len(a["evidence"]) for a in supporting + opposing),
            "gap_detected": "Evidence collection required for all nodes."
        }
    }