from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Unified response format for all LLM providers."""
    content: list[dict]
    stop_reason: str
    raw_response: Any


class LLMService(ABC):
    @abstractmethod
    def add_user_message(self, messages: list, message) -> None:
        pass

    @abstractmethod
    def add_assistant_message(self, messages: list, message) -> None:
        pass

    @abstractmethod
    def text_from_response(self, response: LLMResponse) -> str:
        pass

    @abstractmethod
    def chat(
        self,
        messages: list,
        system: Optional[str] = None,
        temperature: float = 1.0,
        tools: Optional[list] = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    def get_tool_requests(self, response: LLMResponse) -> list[dict]:
        """Extract tool use requests from the response."""
        pass
