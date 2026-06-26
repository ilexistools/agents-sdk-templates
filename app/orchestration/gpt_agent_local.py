import asyncio
import os

from openai import AsyncOpenAI
from agents import Agent, ModelSettings, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStreamableHttp
from pydantic import BaseModel

from app.orchestration.config import load_environment
from app.orchestration.util import load_agent_config


class GPTAgentLocalResponse(BaseModel):
    final_output: str


def _local_base_url() -> str:
    return os.getenv("LOCAL_BASE_URL", "http://localhost:1234/v1")


def _local_api_key() -> str:
    return os.getenv("LOCAL_API_KEY", "lm-studio")


def _local_model() -> str:
    return os.getenv("LOCAL_MODEL_NAME", "local-model")


class GPTLocalAgent(Agent):

    def __init__(self, **kwargs):
        load_environment()

        base_url = kwargs.get("base_url", _local_base_url())
        api_key = kwargs.get("api_key", _local_api_key())
        openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

        self.agent_id = kwargs.get("agent_id", None)
        if self.agent_id is not None:
            config = load_agent_config(self.agent_id, fallback_model=_local_model())
            self.name = config["name"]
            self.role = config["role"]
            instructions_text = config["instructions"]
            model_name = config["model"] or _local_model()
            self.max_output_tokens = config["max_tokens"]
            self.output_type = kwargs.get("output_type", GPTAgentLocalResponse)
            self.tools = kwargs.get("tools", [])
            self.handoffs = kwargs.get("handoffs", [])
            self.mcp_url = kwargs.get("mcp_url")
            self.mcp_headers = kwargs.get("mcp_headers", {})
            self.mcp_timeout = kwargs.get("mcp_timeout", 30)
        else:
            self.name = kwargs.get("name", "GPT Local Agent")
            self.role = kwargs.get("role", "You are a helpful assistant.")
            instructions_text = kwargs.get("instructions", "You are a helpful assistant.")
            self.output_type = kwargs.get("output_type", GPTAgentLocalResponse)
            model_name = kwargs.get("model", _local_model())
            self.max_output_tokens = kwargs.get("max_tokens", 2048)
            self.tools = kwargs.get("tools", [])
            self.handoffs = kwargs.get("handoffs", [])
            self.mcp_url = kwargs.get("mcp_url")
            self.mcp_headers = kwargs.get("mcp_headers", {})
            self.mcp_timeout = kwargs.get("mcp_timeout", 30)

        model_obj = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=openai_client,
        )

        super().__init__(
            name=self.name,
            instructions=self.role + "\n\n" + instructions_text,
            output_type=self.output_type,
            model=model_obj,
            tools=self.tools,
            handoffs=self.handoffs,
            mcp_servers=kwargs.get("mcp_servers", []),
            mcp_config=kwargs.get("mcp_config", {}),
            model_settings=ModelSettings(max_tokens=self.max_output_tokens),
        )

    async def run(self, prompt: str):
        if self.mcp_url:
            async with MCPServerStreamableHttp(
                name="mcp_server",
                params={
                    "url": self.mcp_url,
                    "headers": self.mcp_headers,
                    "timeout": self.mcp_timeout,
                },
                cache_tools_list=True,
                max_retry_attempts=3,
            ) as mcp_server:
                self.mcp_servers = [mcp_server]
                result = await Runner.run(self, prompt)
                return result.final_output

        result = await Runner.run(self, prompt)
        return result.final_output

    def run_sync(self, prompt: str):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run(prompt))

        raise RuntimeError(
            "run_sync() cannot be used inside an active event loop. "
            "Use `await run(prompt)` in async endpoints."
        )
