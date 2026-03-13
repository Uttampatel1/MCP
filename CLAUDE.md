# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Chat is a CLI application for interactive chat with LLM models (Claude or Gemini). It supports document retrieval using `@doc_id` syntax, command-based prompts using `/command`, and extensible tool integrations via MCP (Model Control Protocol).

## Commands

### Run the application
```bash
# With uv (recommended)
uv run main.py

# Without uv
python main.py
```

### Install dependencies
```bash
# With uv
uv pip install -e .

# Without uv
pip install anthropic python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

### Environment setup
Requires `.env` file with:
- `LLM_PROVIDER` - Either "claude" or "gemini" (defaults to "claude")
- `ANTHROPIC_API_KEY` - Anthropic API key (required if using Claude)
- `CLAUDE_MODEL` - Claude model identifier (required if using Claude)
- `GEMINI_API_KEY` - Google Gemini API key (required if using Gemini)
- `GEMINI_MODEL` - Gemini model identifier (required if using Gemini)
- `USE_UV` - Set to "1" to use uv for running MCP server (optional)

## Architecture

### Core Components

- **main.py** - Application entry point. Initializes LLM service (Claude or Gemini based on `LLM_PROVIDER`), MCP clients, and starts the CLI loop. Supports passing additional MCP server scripts as command-line arguments.

- **core/llm_base.py** - `LLMService` abstract base class and `LLMResponse` dataclass defining the unified interface for LLM providers.

- **core/claude.py** - `Claude` class implements `LLMService` for Anthropic. Supports tools, thinking mode, and stop sequences.

- **core/gemini.py** - `Gemini` class implements `LLMService` for Google Gemini. Handles message format conversion between providers.

- **core/chat.py** - `Chat` base class implements the main conversation loop. Processes queries, calls the LLM service, and executes tool requests in a loop until a final response is reached.

- **core/cli_chat.py** - `CliChat` extends `Chat` with document retrieval features. Handles `@doc_id` mentions by fetching document content, and `/command` syntax by calling MCP prompts.

- **core/cli.py** - `CliApp` provides the prompt_toolkit-based interface with autocompletion for commands (`/`) and document references (`@`).

- **core/tools.py** - `ToolManager` aggregates tools from multiple MCP clients and routes tool execution to the correct client.

### MCP Integration

- **mcp_client.py** - `MCPClient` manages connections to MCP servers via stdio. Contains TODOs for implementing `list_tools`, `call_tool`, `list_prompts`, `get_prompt`, and `read_resource`.

- **mcp_server.py** - Sample MCP server using FastMCP. Contains TODOs for implementing document tools, resources, and prompts.

### Message Flow

1. User input is processed by `CliChat._process_query()` which extracts `@mentions` and handles `/commands`
2. `Chat.run()` sends messages to the LLM service with available tools from all MCP clients
3. If the LLM requests tool use, `ToolManager` finds the correct client and executes the tool
4. Loop continues until the LLM returns a final text response

### Key Patterns

- MCP clients are managed via `AsyncExitStack` for proper cleanup
- Multiple MCP servers can run simultaneously (doc_client + additional servers from CLI args)
- Tool discovery is dynamic - tools are fetched from all connected clients before each LLM call
- LLM providers implement `LLMService` interface, allowing easy addition of new providers
