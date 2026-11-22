from fastapi import FastAPI
from pydantic import BaseModel

from app.orchestration.config import load_environment

load_environment()  # so CATALOG_TOKEN and other settings in .env apply from the start

from app.catalog_api import router  # noqa: E402
from app.security import TokenMiddleware  # noqa: E402

class InputRequest(BaseModel):
    data: dict
    
class OutputResponse(BaseModel):
    data: dict
    
app = FastAPI(title='MCP Library')
app.add_middleware(TokenMiddleware)  # no-op unless CATALOG_TOKEN is set
app.include_router(router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/example", response_model=OutputResponse)
async def example_endpoint(payload: InputRequest) -> OutputResponse:
    # Implement your logic here
    return OutputResponse(data={"message": "This is an example response"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8787)
