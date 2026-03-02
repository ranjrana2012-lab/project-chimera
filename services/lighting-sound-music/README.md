# Lighting, Sound & Music Integration Service

## Overview

The Lighting, Sound & Music (LSM) Integration Service provides unified audio generation, processing, and synchronization capabilities for Project Chimera. This service integrates:

- **ACE-Step 1.5**: Open-source music generation model
- **Sound Effects Library**: Pre-defined sound effects for common events
- **Lighting Control**: Synchronized lighting effects with audio
- **Cue System**: Event-driven audio and lighting triggers

## ACE-Step 1.5 Integration

This service integrates [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), a highly efficient open-source music foundation model.

### Features

- Ultra-Fast Generation: Under 2s per full song on A100, under 10s on RTX 3090
- Flexible Duration: Supports 10 seconds to 10 minutes audio generation
- Commercial-Grade Output: Quality beyond most commercial music models
- Rich Style Support: 1000+ instruments and styles
- Multi-Language Lyrics: Supports 50+ languages

### Model Architecture

The service includes the ACE-Step 1.5 model architecture code in:

- `models/` - Model definitions (base, sft, turbo, mlx)
- `acestep-lib/` - Core ACE-Step library code

### Available Models

#### DiT (Diffusion Transformer) Models

| Model | Steps | Quality | Use Case | Hugging Face |
|-------|-------|---------|----------|--------------|
| `acestep-v15-base` | 50 | Medium | All features (text2music, cover, repaint, extract) | [Link](https://huggingface.co/ACE-Step/acestep-v15-base) |
| `acestep-v15-sft` | 50 | High | Text-to-music, cover, repaint | [Link](https://huggingface.co/ACE-Step/acestep-v15-sft) |
| `acestep-v15-turbo` | 8 | Very High | Fast generation (recommended) | [Link](https://huggingface.co/ACE-Step/Ace-Step1.5) |

#### LM (Language Model) Models

| Model | VRAM Requirement | Capabilities | Hugging Face |
|-------|------------------|--------------|--------------|
| `acestep-5Hz-lm-0.6B` | 6-8GB | Basic planning, CoT | [Link](https://huggingface.co/ACE-Step/acestep-5Hz-lm-0.6B) |
| `acestep-5Hz-lm-1.7B` | 8-16GB | Enhanced composition | [Link](https://huggingface.co/ACE-Step/acestep-5Hz-lm-1.7B) |
| `acestep-5Hz-lm-4B` | 24GB+ | Best quality, strong audio understanding | [Link](https://huggingface.co/ACE-Step/acestep-5Hz-lm-4B) |

## Installation

### Prerequisites

- Python 3.11-3.12
- CUDA GPU recommended (also supports MPS / ROCm / Intel XPU / CPU)
- 4GB+ VRAM for basic usage

### Setup

1. **Install dependencies:**

```bash
cd services/lighting-sound-music
pip install -r requirements.txt
```

2. **Download models:**

Models are auto-downloaded from Hugging Face on first use. To pre-download:

```bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='ACE-Step/Ace-Step1.5')
snapshot_download(repo_id='ACE-Step/acestep-5Hz-lm-1.7B')
"
```

3. **Configure model paths:**

Create a `.env` file:

```bash
# DiT model (recommended: turbo for speed)
ACESTEP_CONFIG_PATH=acestep-v15-turbo

# LM model (optional, for advanced features)
ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-1.7B

# Device selection
ACESTEP_DEVICE=auto

# LM backend
ACESTEP_LM_BACKEND=vllm
```

## Usage

### Basic Music Generation

```python
from acestep import AceStepPipeline

# Initialize pipeline
pipeline = AceStepPipeline(
    config_path="acestep-v15-turbo",
    device="auto"
)

# Generate music
result = pipeline.generate(
    prompt="A peaceful ambient track with soft piano and nature sounds",
    duration=30  # seconds
)

# Save result
result.audio.save("output.wav")
```

### Advanced Usage with LM

```python
from acestep import AceStepPipeline

pipeline = AceStepPipeline(
    config_path="acestep-v15-turbo",
    lm_model_path="acestep-5Hz-lm-1.7B",
    lm_backend="vllm"
)

# Generate with Chain-of-Thought planning
result = pipeline.generate(
    prompt="Create a cinematic orchestral piece that builds to a climax",
    duration=120,
    thinking=True,  # Enable LM planning
    format_mode="auto"  # Let LM enhance the prompt
)
```

### Sound Effects

```python
from lsm.sound_effects import SoundEffectsLibrary

# Load sound effects
sfx = SoundEffectsLibrary("assets/sound_effects")

# Play effect
sfx.play("notification_success")
```

### Lighting Synchronization

```python
from lsm.lighting import LightingController
from lsm.cues import CueSystem

# Initialize controllers
lighting = LightingController()
cues = CueSystem()

# Create audio-reactive lighting cue
cue = cues.create_audio_reactive(
    audio_input=result.audio,
    frequency_range="bass",
    effect="pulse"
)

lighting.execute(cue)
```

## API Reference

### Music Generation Endpoints

#### POST /api/music/generate

Generate music from text prompt.

**Request:**
```json
{
  "prompt": "A peaceful ambient track",
  "duration": 30,
  "thinking": false,
  "format_mode": "simple"
}
```

**Response:**
```json
{
  "audio_url": "/tmp/music_20250302_123456.wav",
  "duration": 30.0,
  "sample_rate": 44100,
  "metadata": {
    "bpm": 120,
    "key": "C major",
    "instruments": ["piano", "strings"]
  }
}
```

#### POST /api/music/from_audio

Generate music from reference audio (cover generation).

**Request:**
```json
{
  "audio_url": "/path/to/reference.wav",
  "prompt": "Transform this into a jazz version",
  "duration": 60
}
```

### Sound Effects Endpoints

#### GET /api/sfx/list

List available sound effects.

**Response:**
```json
{
  "effects": [
    {"name": "notification_success", "category": "notification"},
    {"name": "alert_warning", "category": "alert"}
  ]
}
```

#### POST /api/sfx/play

Play a sound effect.

**Request:**
```json
{
  "effect": "notification_success",
  "volume": 0.8
}
```

### Lighting Endpoints

#### POST /api/lighting/set

Set lighting state.

**Request:**
```json
{
  "color": "#FF5733",
  "brightness": 0.8,
  "effect": "pulse"
}
```

#### POST /api/lighting/sync

Synchronize lighting with audio.

**Request:**
```json
{
  "audio_url": "/path/to/audio.wav",
  "mode": "bass_reactive"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACESTEP_CONFIG_PATH` | DiT model to use | `acestep-v15-turbo` |
| `ACESTEP_LM_MODEL_PATH` | LM model to use | `acestep-5Hz-lm-1.7B` |
| `ACESTEP_DEVICE` | Device (auto/cuda/cpu) | `auto` |
| `ACESTEP_LM_BACKEND` | Backend (vllm/pt) | `vllm` |
| `ACESTEP_INIT_LLM` | Initialize LLM (auto/true/false) | `auto` |
| `PORT` | API server port | `8002` |

### GPU Selection

| Your GPU VRAM | Recommended LM Model | Backend |
|---------------|---------------------|---------|
| ≤6GB | None (DiT only) | — |
| 6-8GB | `acestep-5Hz-lm-0.6B` | `pt` |
| 8-16GB | `acestep-5Hz-lm-1.7B` | `vllm` |
| 16-24GB | `acestep-5Hz-lm-1.7B` | `vllm` |
| ≥24GB | `acestep-5Hz-lm-4B` | `vllm` |

## Troubleshooting

### Out of Memory Errors

If you encounter OOM errors:

1. Reduce `ACESTEP_LM_MODEL_PATH` to a smaller model
2. Set `ACESTEP_INIT_LLM=false` to disable LM
3. Reduce batch size in generation requests

### Slow Generation

For faster generation:

1. Use `acestep-v15-turbo` (8 steps vs 50)
2. Disable LM with `ACESTEP_INIT_LLM=false`
3. Use `vllm` backend if available

### Model Download Issues

If models fail to download:

```bash
# Set Hugging Face mirror
export HF_ENDPOINT=https://hf-mirror.com

# Or use ModelScope
export ACESTEP_DOWNLOAD_SOURCE=modelscope
```

## License

ACE-Step 1.5 is licensed under [MIT](https://github.com/ace-step/ACE-Step-1.5/blob/main/LICENSE).

## References

- [ACE-Step 1.5 GitHub](https://github.com/ace-step/ACE-Step-1.5)
- [ACE-Step 1.5 Documentation](https://ace-step.github.io/ace-step-v1.5.github.io/)
- [Hugging Face Models](https://huggingface.co/ACE-Step)
- [Technical Report](https://arxiv.org/abs/2602.00744)
