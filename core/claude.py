from typing import Optional
from anthropic import Anthropic
from anthropic.types import Message
from core.llm_base import LLMService, LLMResponse


class Claude(LLMService):
    def __init__(self, model: str):
        self.client = Anthropic()
        self.model = model

    def add_user_message(self, messages: list, message) -> None:
        if isinstance(message, LLMResponse):
            content = message.content
        elif isinstance(message, Message):
            content = message.content
        else:
            content = message
        messages.append({"role": "user", "content": content})

    def add_assistant_message(self, messages: list, message) -> None:
        if isinstance(message, LLMResponse):
            content = message.content
        elif isinstance(message, Message):
            content = message.content
        else:
            content = message
        messages.append({"role": "assistant", "content": content})

    def text_from_response(self, response: LLMResponse) -> str:
        return "\n".join(
            [block.get("text", "") for block in response.content if block.get("type") == "text"]
        )

    def get_tool_requests(self, response: LLMResponse) -> list[dict]:
        return [block for block in response.content if block.get("type") == "tool_use"]

    def chat(
        self,
        messages: list,
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: list = [],
        tools: Optional[list] = None,
        thinking: bool = False,
        thinking_budget: int = 1024,
    ) -> LLMResponse:
        params = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": messages,
            "temperature": temperature,
            "stop_sequences": stop_sequences,
        }

        if thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }

        if tools:
            params["tools"] = tools

        if system:
            params["system"] = system

        message = self.client.messages.create(**params)

        content = [
            {"type": block.type, **block.model_dump()}
            for block in message.content
        ]

        return LLMResponse(
            content=content,
            stop_reason=message.stop_reason,
            raw_response=message,
        )
