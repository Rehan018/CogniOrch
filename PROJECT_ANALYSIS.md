# CogniOrch - Comprehensive Project Analysis (A-Z)

## 📋 Executive Summary

**CogniOrch** is an advanced AI-powered terminal assistant built with a sophisticated multi-agent architecture. It leverages Chain of Thought (CoT), ReAct patterns, and hierarchical planning to provide intelligent command execution with safety constraints and user approval workflows.

**Core Technology Stack:**
- Python 3.6+
- OpenAI API / LM Studio / Digital Ocean AI integration
- Multi-agent agentic system with orchestration
- Machine Communication Protocol (MCP) for command execution

---

## 🏗️ Architecture Overview

### High-Level Structure

```
CogniOrch
├── Main Entry Point (main.py)
├── Core AI Engine (src/ai_core.py)
├── Terminal Interface Layer (src/terminal_interface.py, terminal_ui.py)
├── Multi-Agent System (src/agents/)
│   ├── Base Agent (base_agent.py)
│   ├── Planner Agent (planner_agent.py)
│   └── Executor Agent (executor_agent.py)
├── Orchestration Layer (src/orchestration/)
│   ├── Orchestrator (orchestrator.py)
│   └── State Manager (state_manager.py)
├── Reasoning Engines (src/reasoning/)
│   ├── Chain of Thought Engine (cot_engine.py)
│   └── ReAct Engine (react_engine.py)
├── MCP Protocol (src/mcp_protocol/)
│   ├── Core Protocol Parser (core.py)
│   ├── Protocol Registry (registry.py)
│   └── Protocol Handlers (handlers/)
├── Command Execution (src/command_executor.py)
├── RAG System (src/rag/knowledge_base.py)
├── Tools System (src/tools/)
├── Safety & Verification (src/verification.py, approval_handler.py)
└── Configuration (config/)
```

---

## 📁 Detailed File-by-File Analysis

### **Root Level Files**

#### `main.py` (Entry Point)
**Purpose:** Main application entry point
**Key Responsibilities:**
- Loads configuration from `config/config.yaml`
- Initializes CogniOrchAI core
- Selects terminal interface (classic or improved)
- Parses command-line arguments (--classic, --version, --debug)
- Handles configuration validation

**Key Dependencies:**
- CogniOrchAI from ai_core.py
- TerminalInterface / ImprovedTerminalUI from terminal interfaces

---

#### `requirements.txt`
**Dependencies:**
```
setuptools==74.1.2      # Package building/distribution
openai==0.28            # OpenAI API client
pyyaml==6.0.1           # YAML configuration parsing
pynput==1.7.7           # Keyboard/mouse input monitoring
httpx==0.28.1           # Modern HTTP client
PyJWT==2.10.1           # JWT token handling
prompt_toolkit==3.0.43  # Interactive CLI toolkit
pygments==2.17.2        # Syntax highlighting
psutil==6.1.1           # System and process utilities
```

---

#### `install.sh`
**Purpose:** Automated installation script for Linux systems
**Features:**
- Python version checking (requires 3.6+)
- Automatic package manager detection (apt, yum, dnf)
- Prerequisite installation (python3-pip, venv, portaudio)
- Virtual environment setup
- Dependency installation
- Configuration file setup

---

### **Configuration Layer** (`config/`)

#### `agent_config.yaml`
**Master configuration file** controlling all system behaviors:

**Feature Toggles:**
- `use_cot: true` - Enable Chain of Thought reasoning
- `use_react: true` - Enable ReAct pattern
- `use_planning: true` - Enable hierarchical planning
- `use_rag: true` - Enable Retrieval Augmented Generation
- `use_multi_agent: true` - Enable multi-agent collaboration

**Component Configurations:**
```yaml
cot:
  verbose: true
  max_steps: 10
  show_reasoning: true

react:
  max_iterations: 10
  enable_tool_calling: true

planner:
  max_plan_steps: 15
  enable_refinement: true

safety:
  enable_verification: true
  require_approval: true
  dangerous_command_patterns:
    - "rm -rf /"
    - "mkfs"
    - "dd if="
```

#### `config.yaml.example`
**Template for user configuration** containing API settings and deployment choices

#### `PrePromt.md`
**System prompt** defining CogniOrch behavior and agentic workflow rules

---

## 🧠 Core AI Engine (`src/`)

### **ai_core.py** - Main AI Orchestrator
**Size:** 728 lines
**Core Class:** `CogniOrchAI`

**Responsibilities:**
1. **Mode Management** - Supports multiple LLM backends:
   - `lm_studio` - Local LLM via LM Studio
   - `digital_ocean` - DigitalOcean AI services
   - Direct OpenAI API

2. **Token Management:**
   - Maintains access tokens for DigitalOcean mode
   - Auto-refreshes tokens every 15 minutes
   - Token validation and renewal logic

3. **Command Approval Workflow:**
   - `require_approval` - User must approve each command
   - `auto_approve_all` - Skip approval for all commands

4. **Streaming Mode:**
   - `is_streaming_mode` - Real-time response streaming

5. **Agentic Components Initialization:**
   - Initializes Orchestrator for multi-agent coordination
   - Creates ExecutorAgent for command execution
   - Configures reasoning engines

**Key Methods:**
```python
__init__(config)              # Initialize with config
_ensure_valid_token()         # Token refresh logic
initialize_context()          # System context setup
query(prompt)                # Process user query
get_conversation_history()   # Retrieve chat history
```

---

### **terminal_interface.py** - Classic Terminal UI
**Size:** ~80 lines
**Class:** `TerminalInterface`

**Features:**
- Readline integration for command history
- Tab completion for commands
- ANSI color formatting
- Agentic loop implementation (auto multi-step execution)
- Command approval tracking
- Error feedback to AI for retry logic

**Agentic Loop Logic:**
```
1. User input → AI query
2. AI generates command → Execute
3. Capture output → Feed back to AI
4. AI analyzes result → Next action
5. Loop until task complete (max 5 iterations)
```

---

### **terminal_ui.py** - Improved Terminal UI
**Advanced terminal interface** using prompt_toolkit with:
- Syntax highlighting
- Better formatting
- Interactive menus
- Progress indicators

---

## 🤖 Multi-Agent System (`src/agents/`)

### **base_agent.py** - Agent Foundation
**Size:** 103 lines
**Abstract Base Class:** `BaseAgent`

**Agent Roles:**
```python
PLANNER     # Plan decomposition
EXECUTOR    # Command execution
VERIFIER    # Result verification
DEBUGGER    # Error diagnosis
OPTIMIZER   # Performance improvement
COORDINATOR # Workflow coordination
```

**Agent States:**
```python
IDLE        # Not active
THINKING    # Processing
ACTING      # Executing
WAITING     # Awaiting response
ERROR       # Error state
```

**Core Methods:**
- `process(task, context)` - Abstract method (implemented by subclasses)
- `can_handle(task)` - Check capability
- `update_state(new_state)` - State management
- `add_to_history(entry)` - Execution tracking
- `get_status()` - Agent status

---

### **planner_agent.py** - Hierarchical Planning Agent
**Size:** 205 lines
**Classes:**
- `PlanStep` - Individual step in execution plan
- `ExecutionPlan` - Complete plan with dependencies
- `PlannerAgent` - Agent that creates plans

**Plan Features:**
```python
step_id          # Unique step identifier
action           # What to execute
rationale        # Why this step
dependencies     # Required prior steps
status           # pending/in_progress/completed/failed
result           # Step output
```

**Functionality:**
- Hierarchical task decomposition
- Dependency management
- Progress tracking
- Plan refinement
- Constraint handling

**Example Plan:**
```
Step 1: Check if tool exists
  ↓ (dependency)
Step 2: Install if missing
  ↓ (dependency)
Step 3: Configure tool
  ↓ (dependency)
Step 4: Verify installation
```

---

### **executor_agent.py** - Command Execution Agent
**Size:** 169 lines
**Class:** `ExecutorAgent`

**Capabilities:**
- Execute, Verify, Retry

**Execution Workflow:**
1. Verify command safety using CommandVerifier
2. Request user approval (if enabled)
3. Execute command with retry logic
4. Monitor for success/failure
5. Return execution result

**Safety Features:**
- Dangerous pattern detection
- User approval requirement
- Retry mechanism (max 3 attempts by default)
- Error recovery

---

## 🎯 Orchestration Layer (`src/orchestration/`)

### **orchestrator.py** - Master Coordinator
**Size:** 303 lines
**Class:** `Orchestrator`

**Responsibilities:**
1. **Agent Management** - Maintains pool of agents
2. **Workflow Selection** - Routes queries to appropriate agent
3. **Reasoning Engine Coordination** - Manages CoT and ReAct
4. **State Management** - Tracks system state
5. **Query Complexity Assessment** - Determines processing strategy

**Processing Strategies:**
```python
HIGH complexity    → Use full planning pipeline
MEDIUM complexity  → Use ReAct loop
LOW complexity     → Direct processing or CoT
```

**Key Methods:**
```python
process_query(query, context)           # Main entry point
_assess_complexity(query)               # Complexity detection
_process_with_planning(query, context)  # Planning mode
_process_with_react(query, context)     # ReAct mode
_process_with_cot(query, context)       # Chain of Thought
_process_direct(query, context)         # Direct processing
```

---

### **state_manager.py** - State Tracking
**Size:** 230 lines
**Class:** `StateManager`

**Tracked State:**
```python
conversation_history    # Chat messages and AI responses
execution_history       # Command executions
agent_states           # Individual agent status
environment_state      # System environment info
goals                  # User objectives
context                # Current context
```

**Features:**
- Session ID generation
- Timestamp tracking
- Metadata attachment
- State persistence (JSON)
- Context management

---

## 💭 Reasoning Engines (`src/reasoning/`)

### **cot_engine.py** - Chain of Thought
**Size:** 134 lines
**Classes:**
- `ThoughtStep` - Individual reasoning step
- `CoTEngine` - CoT processor

**Workflow:**
```
1. Understand the goal
2. Identify required information
3. Plan approach
4. Consider constraints
5. Generate solution
```

**Template-Based Reasoning:**
- Works with LLM to generate multi-step reasoning
- Tracks confidence at each step
- Can display reasoning to user
- Supports up to 10 steps (configurable)

---

### **react_engine.py** - ReAct Pattern
**Size:** 212 lines
**Classes:**
- `ReActStepType` - THOUGHT, ACTION, OBSERVATION
- `ReActStep` - Single loop iteration
- `ReActEngine` - ReAct orchestrator

**The ReAct Loop:**
```
💭 Thought      → LLM reasons about the goal
⚡ Action       → Execute a tool/command
👁️ Observation  → Get feedback from execution
(Loop up to 10 iterations)
```

**Tool Integration:**
- Register callable tools
- Execute actions based on thoughts
- Integrate observations back into loop
- Maximum iteration limit

---

## 🔌 Machine Communication Protocol (`src/mcp_protocol/`)

### **core.py** - MCP Parser
**Size:** 102 lines
**Class:** `MCPProtocol`

**Tag Format:**
```xml
<mcp:protocol_name>command_content</mcp:protocol_name>
```

**Legacy Support:**
```xml
<system>command</system>
<s>command</s>
```

**Key Methods:**
```python
parse_mcp_tags(text)              # Extract all MCP tags
process_response(response, ...)    # Execute handlers
```

**Error Handling:**
- Unknown protocol warnings
- Graceful fallback
- Detailed error logging

---

### **registry.py** - Protocol Handler Registry
**Classes:**
- `ProtocolHandler` - Base handler class
- `ProtocolRegistry` - Handler manager

**Registry Operations:**
```python
register_handler(handler)          # Add new protocol
get_handler(protocol_name)         # Retrieve handler
has_handler(protocol_name)         # Check availability
```

---

### **handlers/terminal_protocol.py** - Terminal Command Handler
**Handles:** `<mcp:terminal>command</mcp:terminal>`

**Execution Pipeline:**
1. Parse command from MCP tag
2. Safety verification via CommandVerifier
3. Request user approval if needed
4. Execute command via PersistentTerminalExecutor
5. Wait for command completion
6. Return output to AI

**Result Dictionary:**
```python
{
    "command": str,           # Original command
    "executed": bool,         # Execution status
    "output": str,            # Command output
    "approved": bool,         # Approval status
    "error": str (optional)   # Error message
}
```

---

## ⚙️ Command Execution (`src/command_executor.py`)

**Size:** 448 lines
**Class:** `PersistentTerminalExecutor`

**Unique Approach:**
- Single persistent terminal window (not launching new terminals)
- FIFO-based command passing
- Process ID tracking
- Automatic terminal cleanup

**Features:**
1. **Terminal Detection:**
   - gnome-terminal
   - konsole
   - xfce4-terminal
   - mate-terminal
   - terminator
   - tilix
   - kitty
   - alacritty
   - x-terminal-emulator (fallback)

2. **Command Execution:**
   - Write command to FIFO
   - Capture output to temp file
   - Wait for completion
   - Retrieve full output

3. **Session Management:**
   - Check for running terminal
   - Reuse existing session
   - Cleanup on exit
   - Lock file management

**Key Methods:**
```python
_initialize_terminal()        # Setup persistent terminal
_is_terminal_running()        # Check terminal status
_detect_terminal_type()       # Detect available terminal
execute_command(command)      # Execute and wait
wait_for_command_completion() # Poll output file
```

---

## 🔐 Safety & Verification (`src/`)

### **verification.py** - Command Safety Checker
**Class:** `CommandVerifier`

**Dangerous Patterns Detected:**
```regex
rm -rf /              # Root deletion
rm -rf /*             # Root wildcard deletion
:(){ :| : & };        # Fork bomb
mkfs                  # Filesystem formatting
dd if=                # Direct disk access
> /dev/sd*            # Device overwriting
chmod 777 /           # Global permission opening
mv /\w+ /dev/null     # System deletion
```

**Verification Result:**
```python
(is_safe, reason)     # Tuple with status and message
```

---

### **approval_handler.py** - User Approval Workflow
**Class:** `ApprovalHandler`

**Features:**
1. **ASCII Box Display:**
   ```
   ╭──────────────────────────────────────────╮
   │ COMMAND APPROVAL REQUIRED                │
   │                                          │
   │ your_command_here                        │
   │                                          │
   ╰──────────────────────────────────────────╯
   ```

2. **Approval Options:**
   - `Y` (default) - Execute command
   - `n` / `no` - Reject command

3. **Settings:**
   - `require_approval` - Enable/disable approval
   - `auto_approve_all` - Skip all approvals

---

## 🗂️ Tools System (`src/tools/`)

### **tool_registry.py** - Tool Management
**Size:** 226 lines
**Classes:**
- `ToolCategory` - Tool categorization enum
- `ToolParameter` - Parameter definition
- `Tool` - Tool specification
- `ToolRegistry` - Tool manager

**Tool Categories:**
```python
FILE_OPERATIONS      # File manipulation
SYSTEM_INFO          # System information
PROCESS_MANAGEMENT   # Process control
NETWORK              # Network operations
PACKAGE_MANAGEMENT   # Package installation
DEVELOPMENT          # Development tools
DATABASE             # Database operations
UTILITY              # Utility functions
```

**Tool Structure:**
```python
{
    "name": str,
    "description": str,
    "category": ToolCategory,
    "parameters": [ToolParameter],
    "function": Callable,
    "examples": [str]
}
```

---

### **file_tools.py** - File Operations
File manipulation tools (read, write, list, delete)

### **system_tools.py** - System Information
System info retrieval (processes, disk space, resources)

---

## 📚 RAG System (`src/rag/`)

### **knowledge_base.py** - Knowledge Management
**Size:** 332 lines
**Classes:**
- `KnowledgeEntry` - Single knowledge piece
- `KnowledgeBase` - Knowledge storage and retrieval

**Knowledge Categories:**
```python
command            # Saved commands
system_info        # System information
error_pattern      # Error patterns
solution           # Solutions to problems
tip                # Helpful tips
documentation      # Documentation
```

**Entry Structure:**
```python
{
    "id": str,              # Unique ID
    "content": str,         # Entry content
    "category": str,        # Category
    "metadata": dict,       # Additional info
    "tags": list,           # Search tags
    "created": timestamp,   # Creation time
    "access_count": int     # Usage count
}
```

**Operations:**
- Add entries
- Retrieve by category
- Search by tags
- Similarity matching
- Persistence (JSON)

---

## 🔑 Token Management (`src/token_manager.py`)

**Size:** 80 lines
**Class:** `TokenManager`

**Purpose:** Manage JWT tokens for DigitalOcean AI API

**Features:**
1. **Token Refresh:**
   - Get refresh token from API
   - Exchange for access token
   - Auto-refresh when expired

2. **Token Caching:**
   - Cache tokens to JSON file
   - Verify token expiration
   - Clear corrupted cache

3. **JWT Validation:**
   - Decode without signature verification
   - Check expiration
   - Handle errors gracefully

**Key Methods:**
```python
_request(method, endpoint, ...)        # API requests
_get_refresh_token()                   # Get refresh token
_get_access_token(refresh_token)       # Get access token
_is_token_expired(token)               # Check expiration
_load_tokens_from_cache()              # Load cached
_save_tokens_to_cache(...)             # Save cache
get_valid_access_token()               # Get current token
```

---

## 🎨 UI Components (`src/`)

### **command_display.py** - Display Formatting
Command output formatting and display

### **interactive_commands.py** - Interactive Features
Interactive command building and suggestions

### **context_manager.py** - Context Handling
Manages conversation and execution context

---

## 🔍 Utility Functions (`src/utils.py`)

**Size:** 181 lines

**Key Functions:**

1. **load_persistent_memory()**
   - Loads system information
   - Creates persistent memory file
   - Includes OS info, kernel, hostname, user
   - Appends distribution information

2. **parse_hooks(text)**
   - Parses MCP protocol tags
   - Uses MCPProtocol parser

3. **extract_context_tags(text)**
   - Extracts content from `<context>` tags

4. **format_output_for_display(output)**
   - Truncates long output
   - Limits line count (default 20)
   - Limits line length (default 80 chars)

---

## 📊 Request-Response Flow

### Complete Execution Flow:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                              │
│    "Install and configure htop"                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR                                            │
│    - Assess complexity                                     │
│    - Route to appropriate processing strategy              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PLANNING AGENT (if complex)                             │
│    - Decompose goal into steps                             │
│    - Create execution plan with dependencies               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM PROCESSING                                          │
│    - Chain of Thought reasoning                            │
│    - Generate reasoning steps                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. MCP PARSING                                             │
│    - Extract <mcp:terminal>command</mcp:terminal>          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. TERMINAL PROTOCOL HANDLER                               │
│    - Verify command safety                                 │
│    - Request user approval                                 │
│    - Execute command                                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. EXECUTOR AGENT                                          │
│    - Run in persistent terminal                            │
│    - Capture output                                        │
│    - Return result                                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. OUTPUT FEEDBACK                                         │
│    - Feed real command output back to AI                   │
│    - AI analyzes result                                    │
│    - Decides next action                                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. DISPLAY TO USER                                         │
│    - Show AI analysis                                      │
│    - Display command output                                │
│    - Ready for next input                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Configuration System

### Configuration Hierarchy:

1. **`config/config.yaml`** - User configuration (main)
   - API endpoints
   - Model selection
   - Approval settings
   - Feature toggles

2. **`config/agent_config.yaml`** - Agent system config
   - Agent settings
   - Reasoning engine params
   - Safety configurations
   - Tool registry

3. **`config/PrePromt.md`** - System prompt
   - Agent behavior rules
   - Communication instructions
   - Workflow guidelines

---

## 🚀 Key Features & Capabilities

### 1. **Multi-Backend Support**
- OpenAI API
- LM Studio (local)
- DigitalOcean AI

### 2. **Advanced Reasoning**
- Chain of Thought (CoT)
- ReAct (Reasoning + Acting)
- Hierarchical planning

### 3. **Safety Features**
- Dangerous pattern detection
- User approval workflows
- Command verification

### 4. **Intelligent Execution**
- Persistent terminal sessions
- Auto-retry on failure
- Error recovery

### 5. **Knowledge Management**
- RAG system for context
- Command history
- Error pattern learning

### 6. **Multi-Agent Orchestration**
- Planner, Executor, Verifier agents
- State management
- Execution tracking

---

## 📈 Data Structures & Models

### Agent State Machine:
```
IDLE ↔ THINKING
      ↓
    ACTING
      ↓
    WAITING
      ↓
    (success) → IDLE
    (error) → ERROR → IDLE
```

### Execution Plan:
```
Goal → Steps (with dependencies)
       ↓
     Step 1 (pending) → in_progress → completed/failed
     Step 2 (pending) → in_progress → completed/failed
     ...
     Completion status & results
```

### Knowledge Entry:
```
UUID → Content
    → Category
    → Metadata
    → Tags
    → Created timestamp
    → Access count
```

---

## 🔗 Dependencies & Integrations

### External APIs:
- **OpenAI** - LLM completions
- **DigitalOcean AI** - Alternative LLM provider

### External Libraries:
- **httpx** - HTTP requests
- **PyJWT** - Token validation
- **prompt_toolkit** - CLI interface
- **psutil** - System monitoring
- **pyyaml** - Configuration parsing

### System Integration:
- Shell/terminal execution
- Process management
- File system access
- System information

---

## 🎯 Usage Patterns

### Simple Query:
```
User: "What's the weather?"
→ Direct LLM response
→ No commands executed
```

### Command Execution:
```
User: "Install htop"
→ LLM generates: <mcp:terminal>sudo apt install htop -y</mcp:terminal>
→ User approval requested
→ Command executed
→ Output returned to AI for analysis
```

### Complex Task:
```
User: "Setup a web server"
→ Orchestrator detects complexity
→ Planner creates multi-step plan
→ Each step executed by Executor
→ Results fed back for next step
→ Final summary to user
```

---

## 🔮 Extensibility Points

1. **Custom Agents**
   - Extend `BaseAgent`
   - Implement `process()` method
   - Register with Orchestrator

2. **Protocol Handlers**
   - Extend `ProtocolHandler`
   - Implement `handle()` method
   - Register with `ProtocolRegistry`

3. **Tools**
   - Define in `ToolRegistry`
   - Implement as callables
   - Add to appropriate categories

4. **Reasoning Engines**
   - Custom CoT implementations
   - Custom ReAct integrations
   - Custom planning strategies

---

## 🐛 Error Handling

### Command Execution Errors:
- Automatic retry (up to 3 attempts)
- Error message feedback to AI
- User notification

### Safety Violations:
- Pattern detection
- User warning
- Still allows override

### API Errors:
- Token refresh on expiration
- Graceful fallback
- Error logging

---

## 📝 Summary Table

| Component | Purpose | Key Class | Size |
|-----------|---------|-----------|------|
| main.py | Entry point | - | Small |
| ai_core.py | Core orchestration | CogniOrchAI | 728 lines |
| terminal_interface.py | UI | TerminalInterface | ~80 lines |
| orchestrator.py | Agent coordination | Orchestrator | 303 lines |
| base_agent.py | Agent foundation | BaseAgent | 103 lines |
| planner_agent.py | Planning | PlannerAgent | 205 lines |
| executor_agent.py | Execution | ExecutorAgent | 169 lines |
| cot_engine.py | Reasoning | CoTEngine | 134 lines |
| react_engine.py | Reasoning | ReActEngine | 212 lines |
| command_executor.py | Execution | PersistentTerminalExecutor | 448 lines |
| core.py (MCP) | Protocol parsing | MCPProtocol | 102 lines |
| knowledge_base.py | Knowledge mgmt | KnowledgeBase | 332 lines |
| state_manager.py | State tracking | StateManager | 230 lines |
| verification.py | Safety | CommandVerifier | Small |
| approval_handler.py | User approval | ApprovalHandler | Small |
| tool_registry.py | Tool management | ToolRegistry | 226 lines |

---

## 🎓 Architectural Patterns Used

1. **Singleton Pattern**
   - MCP instance
   - Token manager

2. **Abstract Factory**
   - Protocol handlers
   - Agents

3. **Registry Pattern**
   - Tool registry
   - Protocol registry
   - Agent registry

4. **State Machine**
   - Agent states
   - Execution states

5. **Template Method**
   - BaseAgent processing
   - Handler interface

6. **Observer Pattern**
   - State changes
   - Event handling

---

## 🚨 Safety & Security

### Command Verification:
- Pattern-based detection
- Dangerous command blocking
- Warning display

### Approval Workflow:
- User must confirm execution
- Detailed command display
- Clear accept/reject options

### Token Management:
- JWT validation
- Expiration checking
- Automatic refresh

### Error Containment:
- Try-catch blocks
- Logging for audit
- User notifications

---

**Project Analysis Complete** ✅

*This analysis covers the entire CogniOrch project architecture, from the main entry point through all major components, libraries, and patterns. The system is designed as a sophisticated AI-powered terminal assistant with advanced reasoning and execution capabilities.*
