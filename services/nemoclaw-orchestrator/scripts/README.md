# NemoClaw Scripts

This directory contains utility scripts for NemoClaw Orchestrator.

## Model Loader Scripts

### model_loader.sh (Bash)

Interactive shell script for managing GGUF models through Ollama.

**Usage:**
```bash
./model_loader.sh [command] [options]
```

**Commands:**
- `list` - List all available models
- `load <model>` - Load a GGUF model into Ollama
- `unload <model>` - Unload a model from Ollama
- `switch <model>` - Switch to a different model (updates .env)
- `test <model>` - Test a model with a simple prompt
- `status` - Show current model status
- `help` - Show help message

**Examples:**
```bash
# List all available models
./model_loader.sh list

# Load Llama 3.1 8B Instruct
./model_loader.sh load llama-3.1-8b-instruct

# Switch to BSL Phase 7 model
./model_loader.sh switch bsl-phase7

# Test a model
./model_loader.sh test llama-3.1-8b-instruct

# Show current status
./model_loader.sh status
```

### model_manager.py (Python)

Programmatic Python utility for model management.

**Usage:**
```bash
./model_manager.py [command] [options]
```

**Commands:**
- `list` - List all available models
- `load <model>` - Load a GGUF model into Ollama
- `unload <model>` - Unload a model from Ollama
- `switch <model>` - Switch to a different model
- `test <model>` - Test a model with a simple prompt
- `status` - Show current status

**Python API:**
```python
from scripts.model_manager import ModelManager

manager = ModelManager()

# List models
for model in manager.list_models("gguf"):
    print(f"{model.name}: {model.description}")

# Load a model
manager.load_model("llama-3.1-8b-instruct")

# Switch to a model
manager.switch_model("llama-3.1-8b-instruct")

# Test a model
manager.test_model("llama-3.1-8b-instruct")

# Get status
status = manager.get_status()
print(f"Current model: {status['current_model']}")
```

## Available GGUF Models

| Model Name | Type | Size | Purpose |
|------------|------|------|---------|
| `llama-3.1-8b-instruct` | General | 4.6 GB | General inference |
| `bsl-phase7` | Specialized | ~4 GB | BSL Phase 7 tasks |
| `bsl-phase8` | Specialized | ~4 GB | BSL Phase 8 tasks |
| `bsl-phase9` | Specialized | ~4 GB | BSL Phase 9 tasks |
| `director-v4` | Specialized | ~4 GB | Director v4 tasks |
| `director-v5` | Specialized | ~4 GB | Director v5 tasks |
| `scenespeak-queryd` | Specialized | ~4 GB | SceneSpeak QueryD tasks |

## Model Location

All GGUF models are stored in:
```
/home/ranj/Project_Chimera_Downloads/LLM Models/gguf/
├── other/           # General purpose models
├── bsl-phases/      # BSL phase models
├── directors/       # Director models
└── scene-speak/     # SceneSpeak models
```

## Requirements

- Ollama service running (`systemctl start ollama`)
- Python 3.10+ for model_manager.py
- Bash 4.0+ for model_loader.sh

## Troubleshooting

### Ollama service not running
```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

### Model fails to load
1. Check GGUF file exists in consolidated location
2. Verify Ollama has sufficient memory
3. Check Ollama logs: `journalctl -u ollama -f`

### Permission denied on scripts
```bash
chmod +x model_loader.sh
chmod +x model_manager.py
```
