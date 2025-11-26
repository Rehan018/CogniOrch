# CogniOrch - Your Intelligent Linux Terminal Assistant

CogniOrch is an AI assistant designed to enhance your Linux terminal experience. It executes commands with explicit approval, analyzes outputs, and can plan multi‑step actions using an agentic workflow. It supports local and cloud backends (LM Studio/Ollama, DigitalOcean/OpenAI/Claude).

## 🌟 Features

- **Intelligent Command Execution**: Understands intent, runs commands, and analyzes results
- **Agentic Workflow (optional)**: Planning, execution, retries with safety checks
- **MCP Protocols**: `terminal`, `files`, `analyze`, `network`, `security`
- **Approval Gating**: Every command requires your approval unless configured
- **Terminal UI**: Classic prompt or improved UI with history, suggestions, and theming
- **Persistent Terminal Execution**: Reuses a dedicated terminal process for commands
- **RAG Knowledge Base**: Records successful executions for reference

## 📦 Prerequisites

- Linux
- Python 3.8+
- Terminal emulator (any of: gnome-terminal, konsole, xfce4-terminal, mate-terminal, terminator, tilix, kitty, alacritty)
- Optional backends:
  - **LM Studio / Ollama** (local) or
  - **DigitalOcean Agents** (cloud via OpenAI/Claude)

## 🚀 Installation

1. Clone the repository

```bash
git clone git@github.com:Rehan018/CogniOrch.git
cd CogniOrch
```

2. Run the installer (creates venv, installs deps, sets alias)

```bash
./install.sh
```

3. Add an alias manually (if needed)

```bash
echo "alias cogniorch='source $(pwd)/venv/bin/activate && python3 $(pwd)/main.py'" >> ~/.bashrc
source ~/.bashrc
```

## ⚙️ Configuration

Create your config file:

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` with one of these modes:

- Local (LM Studio/Ollama)
```yaml
mode: "lm_studio"
api_url: "http://localhost:11434/v1"   # Ollama API or LM Studio API
api_key: "ollama"                       # LM Studio: "lm-studio"
model: "llama3.1:latest"               # Adjust per your local model
stream: true
command_approval:
  require_approval: true
  auto_approve_all: false
use_agentic_mode: true
```

- Cloud (DigitalOcean/OpenAI/Claude via DO Agents)
```yaml
mode: "digital_ocean"
digital_ocean_config:
  agent_id: "your-agent-id"
  agent_key: "your-agent-key"
  agent_endpoint: "https://your-endpoint.app/api/v1"
  model: "gpt-4o-mini"  # example
stream: true
command_approval:
  require_approval: true
  auto_approve_all: false
use_agentic_mode: true
```

Advanced agent settings live in `config/agent_config.yaml`:
- RAG storage path: `~/.cogniorch/knowledge_base.json`
- Log file: `~/.cogniorch/cogniorch.log`

## 🖥️ Usage

- Classic interface
```bash
cogniorch --classic
```

- Improved UI (requires prompt_toolkit/pygments)
```bash
cogniorch
```

You’ll see command proposals enclosed in MCP tags, and an approval prompt:

```
╭──────────────────────────────────────────────────────────────────╮
│ COMMAND APPROVAL REQUIRED
│
│ sudo apt update
│
╰──────────────────────────────────────────────────────────────────╯
  ↳ Execute this command? (Allow/Reject) [Y/n]:
```

- Reply `n` or `no` to deny. CogniOrch will stop and will not escalate with sudo/su.
- On approval, the command runs in a persistent terminal window and the output is streamed back.

## 🧩 MCP Protocols

- `terminal`: Execute shell commands
- `files`: Read/write/append/list files and directories
- `analyze`: One-shot system overview (cpu/mem/disk/network/services)
- `network`: Network operations (ping/trace/scan/lookup/whois)
- `security`: Security checks (users/groups/ports/suid/cron/failed-logins)

Example:
```text
<mcp:terminal>ps aux | head</mcp:terminal>
<mcp:files>read:/etc/hosts</mcp:files>
<mcp:network>scan:192.168.1.0/24</mcp:network>
```

## 🔐 Security Model

- All commands require explicit approval (unless `auto_approve_all: true`)
- Safety verification detects dangerous patterns (e.g., `rm -rf /`)
- Operates with your user privileges by default; denial stops the loop
- Persistent terminal artifacts stored in system temp and ignored by git

## 🧠 Agentic Mode

When `use_agentic_mode: true`:
- The planner can propose steps
- The executor requests approval and runs steps with retries
- After denial: the system stops processing further steps in that response

## 🗂️ Project Structure

- `main.py` – entry point (classic or improved UI)
- `src/ai_core.py` – core AI, MCP integration, approval flow
- `src/mcp_protocol/*` – MCP registry and protocol handlers
- `src/agents/*` – planner/executor agents
- `src/orchestration/*` – orchestrator/state management
- `src/command_executor.py` – persistent terminal executor
- `src/approval_handler.py` – approval prompt
- `src/terminal_interface.py` – classic interface
- `src/terminal_ui.py` – improved UI
- `src/rag/knowledge_base.py` – knowledge base

## 🛠️ Development

- Create a venv and install requirements.txt if not using install.sh
- Run `venv/bin/python main.py --classic` for quick tests
- Logs: `~/.cogniorch/cogniorch.log`

## 🤝 Contributing

PRs and issues are welcome.

## 📜 License

BSD 3‑Clause License. See [LICENSE](LICENSE).
