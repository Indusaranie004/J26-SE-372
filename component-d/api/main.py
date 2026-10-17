# component-d/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from issue_spotting.decomposer import decompose_query
from issue_spotting.models import IssueTreeResponse

app = FastAPI(
    title="Component D - Issue Spotter",
    version="0.1.0",
    description="Legal Issue Spotting & Issue Tree Generation for Sri Lankan Law"
)

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

@app.get("/health")
async def health_check():
    return {
        "status": "Component D is running", 
        "function": "issue_spotting",
        "port": 8003
    }