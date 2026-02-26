# LoRA Adapters

This directory contains fine-tuned LoRA adapters for the language models used in Project Chimera.

## Structure

```
lora-adapters/
├── scenespeak-7b/
│   ├── v1.0.0/
│   │   ├── adapter_config.json
│   │   └── adapter_model.bin
│   └── current -> v1.0.0
└── README.md
```

## scenespeak-7b

**Base Model:** llama-2-7b-hf
**Purpose:** Theatrical dialogue generation
**Version:** 1.0.0

### Metrics
- Perplexity: 12.4
- Character Consistency: 0.87
- Safety Pass Rate: 0.98
- Avg Response Time: 450ms

### Usage

Load the adapter using the Hugging Face transformers library:

```python
from peft import PeftModel, PeftConfig

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("llama-2-7b-hf")

# Load adapter
adapter_path = "models/lora-adapters/scenespeak-7b/current"
model = PeftModel.from_pretrained(base_model, adapter_path)
```

## Training

To train new adapters:

```bash
python scripts/training/train_lora.py \
  --base_model llama-2-7b-hf \
  --data_path data/theatrical_dialogue.jsonl \
  --output_dir models/lora-adapters/scenespeak-7b/v1.0.1 \
  --r 16 \
  --lora_alpha 32 \
  --lora_dropout 0.05
```
