# AI Solution Architecture & Draw.io MCP Integration

Welcome to the **AI Solution Architecture** repository! This repository contains architecture designs, templates, and full integration for the **Draw.io Model Context Protocol (MCP) server** (`@drawio/mcp`), enabling AI assistants (Claude, Cursor, VS Code, Antigravity/Gemini IDE) to programmatically render, view, and modify Draw.io architecture diagrams directly via natural language prompts.

---

## 🚀 Features

- **Draw.io MCP Server Integration**: Pre-configured setup using official `@drawio/mcp` for seamless model context protocol support.
- **Solution Architecture Templates**:
  - [`templates/cloud_architecture.drawio`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/templates/cloud_architecture.drawio): Microservices, API Gateway, Authentication & Multi-tier Data Layer.
  - [`templates/ai_rag_pipeline.drawio`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/templates/ai_rag_pipeline.drawio): End-to-end Data Ingestion & Retrieval-Augmented Generation (RAG) architecture.
- **Multi-Editor Compatibility**: Standalone [`mcp.json`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/mcp.json) and editor config [`.vscode/mcp.json`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/.vscode/mcp.json) for Cursor, Windsurf, VS Code MCP extensions, and Claude Desktop.

---

## 🛠️ Configuration & Setup

### 1. Prerequisites

Ensure **Node.js** (v18 or higher) and **npm** are installed on your machine:
```bash
node -v
npm -v
```

Install local repository dependencies:
```bash
npm install
```

---

### 2. MCP Server Configuration

The repository includes root-level and editor-level MCP server configurations:

#### `mcp.json` / `.vscode/mcp.json`
```json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": [
        "-y",
        "@drawio/mcp"
      ]
    }
  }
}
```

#### Configuring in Claude Desktop
Add the following snippet to your `claude_desktop_config.json`:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["-y", "@drawio/mcp"]
    }
  }
}
```

#### Configuring in Cursor / VS Code
- Open **Settings > MCP Servers** (or `.vscode/mcp.json`).
- Enable `drawio` server.

---

## 💡 Usage & Workflow

Once the Draw.io MCP server is running, you can ask your AI assistant to perform diagramming tasks:

### Prompt Examples

1. **Generate Architecture Diagrams**:
   > *"Create a cloud solution architecture diagram in Draw.io for an event-driven e-commerce microservices platform with Kafka, PostgreSQL, and AWS Lambda."*

2. **Generate AI / LLM Pipelines**:
   > *"Draw a Draw.io sequence diagram showing an LLM agent with web search tool usage and memory persistence."*

3. **Export and Edit Existing Diagrams**:
   > *"Open `templates/ai_rag_pipeline.drawio`, add a hybrid search component (BM25 + Dense Vectors) and save the result."*

---

## 📂 Repository Structure

```
ai-solution-architecture/
├── .vscode/
│   └── mcp.json                    # VS Code & Cursor MCP configuration
├── templates/
│   ├── cloud_architecture.drawio   # Cloud Infrastructure Draw.io XML Template
│   └── ai_rag_pipeline.drawio      # RAG & LLM Pipeline Draw.io XML Template
├── mcp.json                        # Root MCP configuration
├── package.json                    # Node dependencies (@drawio/mcp)
└── README.MD                       # Documentation & usage guide
```

---

## 📜 License

MIT License.
