from google import genai
from google.genai import types
from typing import Optional
from core.llm_base import LLMService, LLMResponse


class Gemini(LLMService):
    def __init__(self, model: str, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def add_user_message(self, messages: list, message) -> None:
        if isinstance(message, LLMResponse):
            content = message.content
        elif isinstance(message, str):
            content = message
        else:
            content = message
        messages.append({"role": "user", "content": content})

    def add_assistant_message(self, messages: list, message) -> None:
        if isinstance(message, LLMResponse):
            content = message.content
        elif isinstance(message, str):
            content = message
        else:
            content = message
        messages.append({"role": "assistant", "content": content})

    def text_from_response(self, response: LLMResponse) -> str:
        texts = []
        for part in response.content:
            if part.get("type") == "text":
                texts.append(part.get("text", ""))
        return "\n".join(texts)

    def _convert_tools_to_gemini_format(self, tools: list) -> list:
        """Convert Anthropic-style tools to Gemini function declarations."""
        if not tools:
            return []

        function_declarations = []
        for tool in tools:
            func_decl = types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("input_schema", {}),
            )
            function_declarations.append(func_decl)

        return function_declarations

    def _convert_messages_to_gemini_format(self, messages: list) -> list:
        """Convert Anthropic-style messages to Gemini format."""
        gemini_messages = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]

            parts = []
            if isinstance(content, str):
                parts = [types.Part.from_text(text=content)]
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(types.Part.from_text(text=block.get("text", "")))
                        elif block.get("type") == "tool_result":
                            parts.append(types.Part.from_text(text=f"Tool result: {block.get('content', '')}"))
                    else:
                        parts.append(types.Part.from_text(text=str(block)))
            else:
                parts = [types.Part.from_text(text=str(content))]

            gemini_messages.append(types.Content(role=role, parts=parts))

        return gemini_messages

    def chat(
        self,
        messages: list,
        system: Optional[str] = None,
        temperature: float = 1.0,
        tools: Optional[list] = None,
    ) -> LLMResponse:
        gemini_messages = self._convert_messages_to_gemini_format(messages)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8000,
        )

        if system:
            config.system_instruction = system

        if tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)
            if gemini_tools:
                config.tools = [types.Tool(function_declarations=gemini_tools)]

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=gemini_messages,
            config=config,
        )

        content = []
        stop_reason = "end_turn"

        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            content.append({"type": "text", "text": part.text})
                        elif hasattr(part, "function_call") and part.function_call:
                            stop_reason = "tool_use"
                            content.append({
                                "type": "tool_use",
                                "id": f"call_{part.function_call.name}",
                                "name": part.function_call.name,
                                "input": dict(part.function_call.args),
                            })

        return LLMResponse(
            content=content,
            stop_reason=stop_reason,
            raw_response=response,
        )

    def get_tool_requests(self, response: LLMResponse) -> list[dict]:
        return [block for block in response.content if block.get("type") == "tool_use"]
