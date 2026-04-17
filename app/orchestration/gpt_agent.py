import asyncio
from dotenv import load_dotenv, find_dotenv
from agents import Agent, Runner, ModelSettings
from pydantic import BaseModel

class GPTAgentResponse(BaseModel):
    final_output: str


class GPTAgent(Agent):
    
    def __init__(self, **kwargs):
        load_dotenv(find_dotenv())
        # Config
        self.name = kwargs.get("name", "GPT Agent")
        self.role = kwargs.get("role", "You are a helpful assistant.")
        self.instructions = kwargs.get("instructions", "You are a helpful assistant.")
        self.output_type = kwargs.get("output_type", GPTAgentResponse)
        self.model = kwargs.get("model", "gpt-4.1-mini")
        self.max_output_tokens = kwargs.get("max_tokens", 2048)
        self.tools = kwargs.get("tools", [])
        self.handoffs = kwargs.get("handoffs", [])

        super().__init__(
            name=self.name,
            instructions=self.role + "\n\n" + self.instructions,
            output_type=self.output_type,
            model=self.model,
            tools=self.tools,
            handoffs=self.handoffs,
            model_settings=ModelSettings(max_tokens=self.max_output_tokens),
        )
    
    async def run(self, prompt):
        result = await Runner.run(self, prompt)
        return result.final_output
    
    def run_sync(self, prompt):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run(prompt))

        raise RuntimeError(
            "run_sync() cannot be used inside an active event loop. "
            "Use `await run(prompt)` in async endpoints."
        )
         
