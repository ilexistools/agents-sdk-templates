from pydantic import BaseModel
from app.orchestration.gpt_agent import GPTAgent


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int


def write_haiku(subject: str):
    evaluator = GPTAgent(agent_id='evaluator', output_type=HaikuResponse)
    writer = GPTAgent(agent_id='writer', output_type=HaikuResponse, handoffs=[evaluator])
    prompt = f"Write a haiku about {subject}."
    result = writer.run_sync(prompt)
    return result


if __name__ == "__main__":
    subject = "the changing seasons"
    result = write_haiku(subject)
    print(result.model_dump())
