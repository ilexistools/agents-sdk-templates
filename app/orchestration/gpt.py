from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel

class GPTResponse(BaseModel):
    final_output: str
    
class GPT:

    def __init__(self, **kwargs):
        load_dotenv(find_dotenv())

        # Clients
        self.client = OpenAI()
        self.async_client = AsyncOpenAI()

        # Config
        self.name = kwargs.get("name", "GPT Agent")
        self.role = kwargs.get("role", "You are a helpful assistant.")
        self.instructions = kwargs.get("instructions", "You are a helpful assistant.")
        self.output_type = kwargs.get("output_type", GPTResponse)
        self.model = kwargs.get("model", "gpt-4.1-mini")
        self.max_output_tokens = kwargs.get("max_tokens", 2048)

    async def run(self, prompt):
        response = await self.async_client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": self.role + "\n\n" + self.instructions},
                {"role": "user", "content": prompt}
            ],
            max_output_tokens=self.max_output_tokens,
            text_format=self.output_type
    
        )
        if response.output_parsed is not None:
            return response.output_parsed
        return self.output_type(final_output=response.output_text)

    def run_sync(self, prompt):
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": self.role + "\n\n" + self.instructions},
                {"role": "user", "content": prompt}
            ],
            max_output_tokens=self.max_output_tokens,
            text_format=self.output_type
    
        )
        if response.output_parsed is not None:
            return response.output_parsed
        return self.output_type(final_output=response.output_text)
