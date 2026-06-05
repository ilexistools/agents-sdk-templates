from fastapi import FastAPI
from pydantic import BaseModel

from app.orchestration import gpt_agent
from app.orchestration.config import default_model
from app.orchestration.util import instruction_loader


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int


class HaikuRequest(BaseModel):
    subject: str


app = FastAPI(title="GPT Agents + FastAPI Example")

MODEL_NAME = default_model()

evaluator = gpt_agent.GPTAgent(
    name="Haiku Evaluator",
    role="You are a strict but helpful haiku reviewer.",
    instructions=instruction_loader("evaluator"),
    output_type=HaikuResponse,
    model=MODEL_NAME,
)

writer = gpt_agent.GPTAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions=instruction_loader("writer"),
    output_type=HaikuResponse,
    handoffs=[evaluator],
    model=MODEL_NAME,
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
