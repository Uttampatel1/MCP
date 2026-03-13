import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude
from core.gemini import Gemini
from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# LLM Provider Config
llm_provider = os.getenv("LLM_PROVIDER", "claude")  # "claude" or "gemini"

# Anthropic Config
claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

# Gemini Config
gemini_model = os.getenv("GEMINI_MODEL", "")
gemini_api_key = os.getenv("GEMINI_API_KEY", "")

if llm_provider == "claude":
    assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
    assert anthropic_api_key, "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
elif llm_provider == "gemini":
    assert gemini_model, "Error: GEMINI_MODEL cannot be empty. Update .env"
    assert gemini_api_key, "Error: GEMINI_API_KEY cannot be empty. Update .env"
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {llm_provider}. Use 'claude' or 'gemini'.")


async def main():
    if llm_provider == "claude":
        llm_service = Claude(model=claude_model)
    else:
        llm_service = Gemini(model=gemini_model, api_key=gemini_api_key)

    server_scripts = sys.argv[1:]
    clients = {}

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            llm_service=llm_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
