from fastapi import FastAPI
from pydantic import BaseModel

from app.orchestration import gpt_agent
from app.orchestration.util import instruction_loader


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int


class HaikuRequest(BaseModel):
    subject: str


app = FastAPI(title="GPT Agents + FastAPI Example")


evaluator = gpt_agent.GPTAgent(
    name="Haiku Evaluator",
    role="You are a strict but helpful haiku reviewer.",
    instructions=instruction_loader("evaluator"),
    output_type=HaikuResponse,
    model="gpt-4.1-mini",
)

writer = gpt_agent.GPTAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions=instruction_loader("writer"),
    output_type=HaikuResponse,
    handoffs=[evaluator],
    model="gpt-4.1-mini",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/haiku", response_model=HaikuResponse)
async def write_haiku(payload: HaikuRequest) -> HaikuResponse:
    prompt = f"Write a haiku about {payload.subject}."
    result = await writer.run(prompt)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 