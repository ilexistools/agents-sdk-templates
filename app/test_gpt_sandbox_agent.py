from pydantic import BaseModel
from app.orchestration import gpt_sandbox_agent


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int

writer = gpt_sandbox_agent.GPTSandboxAgent(
    agent_id="writer",
    output_type=HaikuResponse,
)

def write_haiku(subject: str):
    prompt = f"Write a haiku about {subject}."
    result = writer.run_sync(prompt)
    return result

if __name__ == "__main__":
    subject = "the changing seasons"
    result = write_haiku(subject)
    print(result.model_dump())
