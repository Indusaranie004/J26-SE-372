# component-d/issue_spotting/decomposer.py

import os
import re
import json
from dotenv import load_dotenv

# Import Pydantic models, prompts, and mock data
from .models import IssueTreeResponse
from .prompts import build_messages
from .mock_data import MOCK_ISSUE_TREE

# Load environment variables
load_dotenv()

# --- MOCK MODE TOGGLE (Matches Component A's convention) ---
MOCK_MODE = os.getenv("COMPONENT_D_MOCK", "true").lower() == "true"

# Only initialize Groq if we are NOT in mock mode
if not MOCK_MODE:
    from groq import Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    print("[INFO] Component D initialized with Groq API (Real Mode).")
else:
    print("[INFO] Component D initialized in MOCK_MODE. Bypassing Groq API.")


def decompose_query(raw_query: str) -> IssueTreeResponse:
    """
    Function 1: Legal Issue Spotting & Issue Tree Generation.
    
    If MOCK_MODE=true, returns the hardcoded mock data.
    If MOCK_MODE=false, calls the Groq API (Llama-3.3-70B).
    If the API fails, it automatically falls back to mock data to prevent crashes.
    """
    
    # ==========================================
    # 1. MOCK MODE PIPELINE
    # ==========================================
    if MOCK_MODE:
        # Create a copy so we don't mutate the original mock dictionary
        mock_response = MOCK_ISSUE_TREE.copy()
        
        # Update the query to match the user's input for realism
        mock_response["query"] = raw_query 
        
        # Validate and return via Pydantic
        return IssueTreeResponse(**mock_response)

    # ==========================================
    # 2. REAL API PIPELINE (Groq)
    # ==========================================
    messages = build_messages(raw_query)

    try:
        # Call the Groq API
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",  
            messages=messages,
            temperature=0.1,       # Low temp for consistent JSON
            max_tokens=2000,       
            response_format={"type": "json_object"}, 
            timeout=30             # Fail fast if API hangs
        )

        raw_json_string = completion.choices[0].message.content

        # Robust JSON Parsing (strips markdown fences if the LLM adds them)
        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json_string.strip(), flags=re.IGNORECASE)

        try:
            parsed_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Fallback: Find the outermost valid JSON object in the text
            start = cleaned_text.find("{")
            end = cleaned_text.rfind("}")
            if start != -1 and end > start:
                parsed_data = json.loads(cleaned_text[start:end+1])
            else:
                raise ValueError("Could not extract valid JSON from LLM response.")

        # Validate and return via Pydantic
        return IssueTreeResponse(**parsed_data)

    # ==========================================
    # 3. AUTOMATIC FALLBACK (Safety Net)
    # ==========================================
    except Exception as e:
        print(f"[ERROR] Groq API failed: {str(e)}")
        print("[INFO] Falling back to MOCK data to prevent app crash.")
        
        mock_response = MOCK_ISSUE_TREE.copy()
        mock_response["query"] = raw_query
        return IssueTreeResponse(**mock_response)