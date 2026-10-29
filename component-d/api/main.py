# component-d/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel
from issue_spotting.decomposer import decompose_query
from issue_spotting.models import IssueTreeResponse
from argument_mapping.mapper import build_argument_map

app = FastAPI(
    title="Component D - Issue Spotter & Argument Map",
    version="0.1.0",
    description="Legal Issue Spotting, Argument Map Generation & Citation Strength Prediction for Sri Lankan Law"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# FUNCTION 1: ISSUE SPOTTING
# ==============================================================================

class QueryRequest(BaseModel):
    query: str

@app.post("/analyze", response_model=IssueTreeResponse)
async def run_analysis(request: QueryRequest):
    """
    Endpoint for the UI to send a raw query and get the Issue Tree.
    """
    # Basic validation
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")
        
    print(f"\n[INFO] Received query: {request.query}")
    
    # Call the backend logic
    result = decompose_query(request.query)
    
    return result

# ==============================================================================
# FUNCTION 2: ARGUMENT MAP & CITATION STRENGTH
# ==============================================================================

class ArgumentMapRequest(BaseModel):
    issue_id: str
    issue_question: str

@app.post("/generate-argument-map")
async def generate_argument_map(request: ArgumentMapRequest):
    """
    Generates a dynamic Argument Map with real-time XGBoost-predicted 
    citation strength scores and SHAP explanations.
    """
    if not request.issue_question.strip():
        raise HTTPException(status_code=422, detail="Issue question cannot be empty")
        
    print(f"\n[INFO] Generating argument map for issue: {request.issue_id}")
    
    try:
        # This triggers the LLM -> Component A -> XGBoost pipeline
        map_data = build_argument_map(
            issue_id=request.issue_id,
            issue_question=request.issue_question
        )
        return {"status": "success", "data": map_data}
    except Exception as e:
        print(f"[ERROR] Argument map generation failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
    
# ==============================================================================
# HEALTH CHECK
# ==============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "Component D is running", 
        "function": "issue_spotting",
        "port": 8003
    }