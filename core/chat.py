from mcp_client import MCPClient
from core.tools import ToolManager
from core.llm_base import LLMService


class Chat:
    def __init__(self, llm_service: LLMService, clients: dict[str, MCPClient]):
        self.llm_service: LLMService = llm_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[dict] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            response = self.llm_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            self.llm_service.add_assistant_message(self.messages, response)

            if response.stop_reason == "tool_use":
                print(self.llm_service.text_from_response(response))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response, self.llm_service
                )

                self.llm_service.add_user_message(
                    self.messages, tool_result_parts
                )
            else:
                final_text_response = self.llm_service.text_from_response(
                    response
                )
                break

        return final_text_response
