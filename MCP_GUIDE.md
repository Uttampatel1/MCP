# Understanding MCP (Model Context Protocol)

## What is MCP?

MCP is a protocol that allows AI models (like Claude or Gemini) to interact with external tools, data sources, and services. Think of it as a bridge between the AI and the outside world.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   AI Model  │ ←────── │ MCP Client  │ ←────── │ MCP Server  │
│ (Claude/    │         │ (Your App)  │         │ (Tools &    │
│  Gemini)    │         │             │         │  Resources) │
└─────────────┘         └─────────────┘         └─────────────┘
```

## Three Core Concepts

### 1. Tools
Functions that the AI can call to perform actions.

```python
@mcp.tool(
    name="read_doc_content",
    description="Reads the content of a document given its name.",
)
def read_doc_content(
    doc_id: str = Field(description="The name of the document to read."),
) -> str:
    return docs[doc_id]
```

**How it works:**
1. AI sees the tool and its description
2. AI decides to use the tool based on user's request
3. AI calls the tool with parameters
4. Tool returns result to AI
5. AI uses result to form response

### 2. Resources
Data that can be read by the AI. Like files or databases.

```python
# List all documents
@mcp.resource("docs://documents")
def list_docs() -> list[str]:
    return list(docs.keys())

# Get specific document content
@mcp.resource("docs://documents/{doc_id}")
def get_doc_content(doc_id: str) -> str:
    return docs[doc_id]
```

**URI patterns:**
- `docs://documents` - returns all document IDs
- `docs://documents/report.pdf` - returns content of report.pdf

### 3. Prompts
Pre-defined conversation templates that guide the AI.

```python
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format."
)
def format_document(doc_id: str) -> list[Message]:
    return [
        UserMessage(f"Reformat document {doc_id} to markdown...")
    ]
```

**Usage:** User types `/format report.pdf` and the prompt template is sent to the AI.

## MCP Architecture in This Project

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│  - Creates LLM service (Claude/Gemini)                      │
│  - Creates MCP clients                                      │
│  - Starts CLI                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       MCPClient                             │
│  mcp_client.py                                              │
│  - Connects to MCP servers via stdio                        │
│  - Methods: list_tools(), call_tool(), list_prompts(),      │
│             get_prompt(), read_resource()                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       MCP Server                            │
│  mcp_server.py                                              │
│  - Defines tools, resources, and prompts                    │
│  - Runs as separate process                                 │
│  - Communicates via stdin/stdout                            │
└─────────────────────────────────────────────────────────────┘
```

## Communication Flow

### Tool Call Example

```
User: "What's in the report.pdf?"

1. CliChat sends query to LLM
2. LLM sees available tools (from ToolManager.get_all_tools())
3. LLM responds: "I'll use read_doc_content tool"
4. ToolManager.execute_tool_requests() calls the tool
5. MCPClient.call_tool("read_doc_content", {"doc_id": "report.pdf"})
6. MCP Server executes the function and returns content
7. Result sent back to LLM
8. LLM forms final response to user
```

### Resource Fetch Example

```
User: "Tell me about @report.pdf"

1. CliChat detects @mention
2. Calls MCPClient.read_resource("docs://documents/report.pdf")
3. MCP Server returns document content
4. Content injected into prompt as context
5. LLM responds with knowledge of document
```

## Creating Your Own MCP Server

```python
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("MyServer")

# Define a tool
@mcp.tool(name="greet", description="Says hello")
def greet(name: str = Field(description="Name to greet")) -> str:
    return f"Hello, {name}!"

# Define a resource
@mcp.resource("data://users")
def get_users() -> list[str]:
    return ["Alice", "Bob", "Charlie"]

# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Implementing MCPClient Methods

The `mcp_client.py` has TODOs to implement. Here's how:

```python
async def list_tools(self) -> list[types.Tool]:
    result = await self.session().list_tools()
    return result.tools

async def call_tool(self, tool_name: str, tool_input: dict):
    result = await self.session().call_tool(tool_name, tool_input)
    return result

async def list_prompts(self) -> list[types.Prompt]:
    result = await self.session().list_prompts()
    return result.prompts

async def get_prompt(self, prompt_name: str, args: dict):
    result = await self.session().get_prompt(prompt_name, args)
    return result.messages

async def read_resource(self, uri: str):
    result = await self.session().read_resource(uri)
    # Parse based on content type
    content = result.contents[0]
    if hasattr(content, 'text'):
        return content.text
    return content
```

## Key Files Summary

| File | Purpose |
|------|---------|
| `mcp_server.py` | Defines tools, resources, prompts |
| `mcp_client.py` | Connects to MCP servers, calls their methods |
| `core/tools.py` | Manages tools from multiple MCP clients |
| `core/chat.py` | Main loop that uses tools based on LLM responses |
| `core/cli_chat.py` | Handles `@mentions` and `/commands` |

## Quick Reference

| Concept | Decorator | Purpose | Example |
|---------|-----------|---------|---------|
| Tool | `@mcp.tool()` | AI calls to perform action | Edit file, search web |
| Resource | `@mcp.resource()` | AI reads data | Get file content, list items |
| Prompt | `@mcp.prompt()` | Pre-defined templates | `/summarize`, `/format` |

## Tips

1. **Tool descriptions matter** - The AI uses them to decide when to call tools
2. **Use Field() for parameters** - Provides descriptions for each parameter
3. **Resources are read-only** - Use tools for write operations
4. **Prompts save repetition** - Create templates for common tasks
5. **Multiple servers OK** - You can connect to many MCP servers at once
