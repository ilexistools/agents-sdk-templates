from pydantic import BaseModel
from app.orchestration import gpt_sandbox_agent
from app.orchestration.config import sandbox_model
from app.orchestration.util import instruction_loader

class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int

writer = gpt_sandbox_agent.GPTSandboxAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions=instruction_loader("writer"),
    output_type=HaikuResponse,
    model=sandbox_model(),
    skills_dir='app/assets/skills',
)

def write_haiku(subject: str):
    prompt = f"Write a haiku about {subject}."
    result = writer.run_sync(prompt)
    return result

if __name__ == "__main__":
    subject = "the changing seasons"
    result = write_haiku(subject)
    print(result.model_dump())
