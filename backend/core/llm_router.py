from dataclasses import dataclass
from typing import Optional, Any, List, Dict
from enum import Enum
from dataclasses import dataclass

class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    role: LLMRole
    content: str

# -----------------------------
# Request / Response Objects
# -----------------------------

class LLMRequest:
    def __init__(self, messages: list[LLMMessage], system_prompt: str | None = None):
        self.messages = messages
        self.system_prompt = system_prompt

@dataclass
class LLMResponse:
    content: str
    provider: str
    raw: Optional[Any] = None


# -----------------------------
# Base Provider
# -----------------------------

class BaseProvider:
    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError()


# -----------------------------
# OpenAI Provider
# -----------------------------

class OpenAIProvider(BaseProvider):

    async def complete(self, request: LLMRequest) -> LLMResponse:

        import openai

        client = openai.AsyncOpenAI()

        messages = request.messages

        # add system prompt if provided
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            provider="openai",
            raw=response
        )


# -----------------------------
# Provider Registry
# -----------------------------

PROVIDERS = {
    "openai": OpenAIProvider
}


# -----------------------------
# LLM Router
# -----------------------------

class LLMRouter:

    def __init__(self):
        self.providers = {}

    def register(self, name: str, provider: BaseProvider):
        self.providers[name] = provider

    async def complete(self, request: LLMRequest, provider: str = "openai") -> LLMResponse:

        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not registered")

        p = self.providers[provider]

        return await p.complete(request)


# -----------------------------
# Global Router Instance
# -----------------------------

llm_router = LLMRouter()

# register default provider
llm_router.register("openai", OpenAIProvider())


# -----------------------------
# FastAPI Dependency Helper
# -----------------------------

def get_llm_router() -> LLMRouter:
    return llm_router