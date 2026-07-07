from fastapi import FastAPI
from pydantic import BaseModel

class InputRequest(BaseModel):
    data: dict
    
class OutputResponse(BaseModel):
    data: dict
    
app = FastAPI(title="GPT Agents + FastAPI Example")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/example", response_model=OutputResponse)
async def example_endpoint(payload: InputRequest) -> OutputResponse:
    # Implement your logic here
    return OutputResponse(data={"message": "This is an example response"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
