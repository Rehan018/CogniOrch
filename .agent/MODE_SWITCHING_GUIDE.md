# 🔄 Mode Switching Guide - CogniOrch

## Overview

CogniOrch has **two execution modes**:

- 🚀 **Simple Mode**: Fast, single-command execution
- 🧠 **Planning Mode**: Full CoT reasoning + multi-step plans

The system **automatically** chooses the best mode based on your task.

---

## 🎯 Quick Reference

### Trigger Planning Mode (Complex Tasks)

Use these keywords in your request:

- ✅ `setup`
- ✅ `install and configure`
- ✅ `deploy`
- ✅ `create a project`
- ✅ `build and test`
- ✅ `troubleshoot`
- ✅ `debug`
- ✅ `analyze and fix`
- ✅ `then` / `after that`
- ✅ `multiple steps`

### Trigger Simple Mode (Fast Tasks)

Use these keywords in your request:

- ✅ `what is`
- ✅ `show me`
- ✅ `list`
- ✅ `display`
- ✅ `check if`
- ✅ `tell me`

---

## 📝 Examples

### ➡️ Planning Mode Examples

**Example 1:**

```
User: "setup a python development environment"
Result: 🧠 AGENTIC PLANNING MODE ACTIVATED
```

**Example 2:**

```
User: "install docker and then create a container"
Result: 🧠 AGENTIC PLANNING MODE ACTIVATED
(Triggered by "install" + "then")
```

**Example 3:**

```
User: "troubleshoot why nginx won't start"
Result: 🧠 AGENTIC PLANNING MODE ACTIVATED
(Triggered by "troubleshoot")
```

### ➡️ Simple Mode Examples

**Example 1:**

```
User: "check if docker is installed"
Result: Simple execution - <mcp:terminal>which docker</mcp:terminal>
```

**Example 2:**

```
User: "show me running processes"
Result: Simple execution - <mcp:terminal>ps aux</mcp:terminal>
```

**Example 3:**

```
User: "what is my IP address"
Result: Simple execution - <mcp:terminal>hostname -I</mcp:terminal>
```

---

## ⚙️ Configuration Control

### Option 1: Global Disable (Config File)

Edit `config/agent_config.yaml`:

```yaml
# Disable all planning mode (always use simple)
use_planning: false

# Enable planning mode (default)
use_planning: true
```

After changing, restart CogniOrch:

```bash
venv/bin/python main.py --classic
```

### Option 2: Runtime Control (Code)

Add a command-line flag to `main.py`:

```python
# In main.py
parser.add_argument('--mode', choices=['simple', 'auto'], 
                    default='auto',
                    help='Execution mode (simple=fast, auto=intelligent)')

# Then pass to CogniOrchAI
config['force_simple_mode'] = (args.mode == 'simple')
```

Then use:

```bash
# Always use simple mode
venv/bin/python main.py --classic --mode simple

# Auto-detect (default)
venv/bin/python main.py --classic --mode auto
```

### Option 3: Interactive Toggle

Add a command in the terminal interface:

```python
# Add to terminal_interface.py commands list
elif user_input.lower() == 'mode planning':
    self.ai_terminal.force_planning = True
    print("Switched to Planning Mode")

elif user_input.lower() == 'mode simple':
    self.ai_terminal.force_planning = False
    print("Switched to Simple Mode")

elif user_input.lower() == 'mode auto':
    self.ai_terminal.force_planning = None  # Auto-detect
    print("Switched to Auto Mode")
```

---

## 🔍 How to Check Current Mode

The system will show you which mode it's using:

**Planning Mode Shows:**

```
============================================================
🧠 AGENTIC PLANNING MODE ACTIVATED
============================================================
```

**Simple Mode Shows:**

```
CogniOrch: <mcp:terminal>command</mcp:terminal>
(No banner)
```

**In Logs:**

```bash
# Check logs to see mode selection
tail -f ~/.cogniorch/cogniorch.log | grep "Using"

# You'll see:
INFO - Using full agentic planning mode
# or
INFO - Using simple agentic loop
```

---

## 🎨 Customizing Complexity Detection

Want to adjust which keywords trigger planning mode?

Edit `src/ai_core.py` in the `_assess_task_complexity()` method:

```python
def _assess_task_complexity(self, prompt):
    """
    Assess if a task needs full planning or simple execution.
    """
    prompt_lower = prompt.lower()
    
    # Add your own high complexity triggers
    high_indicators = [
        "install and configure",
        "setup",
        "deploy",
        # Add more here:
        "migrate",
        "upgrade system",
        "backup and restore",
        "YOUR_CUSTOM_KEYWORD"
    ]
    
    # Add your own simple triggers
    low_indicators = [
        "what is",
        "show me",
        "list",
        # Add more here:
        "count",
        "find",
        "YOUR_CUSTOM_KEYWORD"
    ]
    
    if any(ind in prompt_lower for ind in high_indicators):
        return "high"  # Planning mode
    elif any(ind in prompt_lower for ind in low_indicators):
        return "low"   # Simple mode
    else:
        return "medium"  # Default to simple
```

---

## 💡 Pro Tips

### Tip 1: Force Planning Mode

If auto-detection doesn't trigger planning, add "setup" to your phrase:

```
"setup: check system status"  # Forces planning even for simple task
```

### Tip 2: Force Simple Mode

If you want fast execution for a complex task:

```
"show me nginx config"  # Uses "show me" → simple mode
```

### Tip 3: Chain Complex Tasks

Planning mode shines with multi-step tasks:

```
"install nginx, configure reverse proxy, then test it"
```

### Tip 4: Use Context

The AI remembers context, so you can break complex tasks:

```
Turn 1: "check if nginx is installed"  # Simple mode
Turn 2: "install and configure it"     # Planning mode (knows context)
```

---

## 🐛 Troubleshooting

### Problem: Always using Planning Mode (too slow)

**Solution**: Add keywords from simple triggers:

```
Instead of: "get the current time"
Use: "show me the current time"
```

### Problem: Never using Planning Mode

**Solution 1**: Check config:

```yaml
# In agent_config.yaml
use_planning: true  # Make sure this is true
```

**Solution 2**: Use planning triggers:

```
Instead of: "install nginx"
Use: "setup nginx server"
```

### Problem: Want manual control

**Solution**: Implement Option 3 (Interactive Toggle) above

---

## 📊 Mode Comparison

| Feature | Simple Mode | Planning Mode |
|---------|-------------|---------------|
| **Speed** | ⚡ Very Fast | 🐢 Slower (2-3x) |
| **Reasoning** | ❌ Hidden | ✅ Visible CoT |
| **Planning** | ❌ No plan | ✅ Multi-step plan |
| **Progress** | ❌ No tracking | ✅ Step counter |
| **Best For** | Single commands | Multi-step tasks |
| **Token Usage** | 💰 Low | 💸 Higher |

---

## 🚀 Recommended Usage

**Use Simple Mode For:**

- ✅ Quick checks (is X installed?)
- ✅ Single commands
- ✅ Information queries
- ✅ Fast exploration

**Use Planning Mode For:**

- ✅ System setup tasks
- ✅ Troubleshooting issues
- ✅ Multi-step workflows
- ✅ Complex configurations
- ✅ When you want to see AI's reasoning

---

## 📝 Summary

**Default Behavior**: Auto-detect (recommended)

- System chooses based on keywords
- Smart and efficient

**Manual Control**: 3 options

1. Use keywords to influence mode
2. Config file (`use_planning: false`)
3. Add runtime flags (requires code edit)

**Check Mode**: Look for planning banner or check logs

**Customize**: Edit `_assess_task_complexity()` in `ai_core.py`

---

**Need Help?**
Run these commands to see mode behavior:

```bash
# Test simple mode
You: "check if htop is installed"

# Test planning mode  
You: "setup a test environment"

# Check logs
tail -f ~/.cogniorch/cogniorch.log | grep "mode"
```
