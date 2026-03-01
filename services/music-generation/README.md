# Music Generation Service

Port 8011 - Model inference service for AI music generation.

## Models
- Meta MusicGen-Small (~2GB VRAM)
- ACE-Step (<4GB VRAM)

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Running

```bash
uvicorn music_generation.main:app --host 0.0.0.0 --port 8011
```
