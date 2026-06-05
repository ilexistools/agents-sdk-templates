from pydantic import BaseModel

from app.orchestration import gpt_agent
from app.orchestration.config import default_model
from app.orchestration.util import instruction_loader


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int


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


def write_haiku(subject: str):
    prompt = f"Write a haiku about {subject}."
    result = writer.run_sync(prompt)
    return result


if __name__ == "__main__":
    subject = "the changing seasons"
    result = write_haiku(subject)
    print(result.model_dump())
