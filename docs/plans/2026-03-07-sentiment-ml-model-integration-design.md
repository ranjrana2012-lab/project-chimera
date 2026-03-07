# Sentiment Agent ML Model Integration Design

**Date:** March 7, 2026
**Status:** Design Approved
**Goal:** Replace rule-based sentiment analysis with DistilBERT ML model for improved accuracy

---

## Overview

Replace the existing rule-based sentiment analysis (keyword matching) with a proper ML model using DistilBERT fine-tuned on SST-2. This will significantly improve sentiment classification accuracy for the Sentiment Agent.

**Key Decision:** ML-only approach - remove all rule-based code. Service requires ML model to function.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Sentiment Agent (Port 8004)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   ML Model   │  │   Request    │  │   Response      │  │
│  │   Loader     │──│   Handler    │──│   Formatter    │  │
│  │              │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│        ↓                  ↓                                      │
│  DistilBERT         Text Input                              │
│  (SST-2)            Sentiment Output                         │
│  ~250MB                                                     │
└─────────────────────────────────────────────────────────────┘
```

**Design Decisions:**
- ML-only service (no rule-based fallback)
- Hybrid GPU/CPU support with auto-detection
- Model downloaded during Docker build time
- Lazy loading on first request
- ARM64-optimized for GB10 GPU

---

## Components

### 1. ML Model Wrapper (`ml_model.py` - new file)

```python
"""ML Model Wrapper for Sentiment Analysis."""

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SentimentModel:
    """DistilBERT SST-2 model wrapper for sentiment analysis."""

    MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

    def __init__(self, cache_dir: str = "./models_cache", device: str = "auto"):
        """Initialize model with lazy loading."""
        self.cache_dir = cache_dir
        self.device = self._detect_device() if device == "auto" else device
        self.model = None
        self.tokenizer = None

    def _detect_device(self) -> str:
        """Auto-detect available device."""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def load(self):
        """Load model and tokenizer."""
        logger.info(f"Loading {self.MODEL_NAME} on {self.device}")
        self.tokenizer = DistilBertTokenizer.from_pretrained(
            self.MODEL_NAME, cache_dir=self.cache_dir
        )
        self.model = DistilBertForSequenceClassification.from_pretrained(
            self.MODEL_NAME, cache_dir=self.cache_dir
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model loaded successfully")

    def analyze(self, text: str) -> dict:
        """Analyze sentiment of text."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # Convert to sentiment
        negative_prob = predictions[0][0].item()
        positive_prob = predictions[0][1].item()

        if positive_prob > 0.6:
            sentiment = "positive"
            score = positive_prob
        elif negative_prob > 0.6:
            sentiment = "negative"
            score = 1.0 - negative_prob
        else:
            sentiment = "neutral"
            score = 0.5

        confidence = max(positive_prob, negative_prob)

        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence
        }

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Analyze multiple texts."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)
        return results
```

### 2. Updated Sentiment Analyzer (`sentiment_analyzer.py` - modify)

**Remove:**
- All keyword constants (POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, EMOTION_KEYWORDS)
- All rule-based methods (_analyze_rule_based, _calculate_emotions, _neutral_result)
- Emotion-related code

**Keep:**
- SentimentAnalyzer class structure
- analyze() and analyze_batch() methods (simplified)

**New implementation:**
```python
def __init__(self, use_ml_model: bool = True):
    from ml_model import SentimentModel
    self.model = SentimentModel()
    self.model_available = True

def analyze(self, text: str) -> Dict:
    if not text or not text.strip():
        return self._neutral_result()

    return self.model.analyze(text)
```

### 3. Model Download Script (`scripts/download-model.sh`)

```bash
#!/bin/bash
# Download DistilBERT model for Docker build

set -e

MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english"
CACHE_DIR="./models_cache"

echo "Downloading $MODEL_NAME..."
mkdir -p "$CACHE_DIR"

python3 << EOF
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
print(f"Downloading {MODEL_NAME}...")
tokenizer = DistilBertTokenizer.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
model = DistilBertForSequenceClassification.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
print("Download complete!")
EOF

echo "Model downloaded to $CACHE_DIR"
```

### 4. Updated Configuration (`config.py`)

```python
# Model Configuration
use_ml_model: bool = True  # Forced to True for ML-only approach
model_path: Optional[str] = None  # Not used, using HuggingFace
model_cache_dir: str = "./models_cache"
device: str = "auto"  # Auto-detect cuda/cpu
```

### 5. Updated Requirements (`requirements.txt`)

```python
# ML/NLP
transformers==4.36.0
torch==2.1.0  # ARM64 compatible
```

---

## Data Flow

```
┌──────────────┐
│ Client Request│
│ POST /analyze │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Handler                                             │
│  • Validate request (text, max_length)                      │
│  • Check model loaded (lazy load if first request)          │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  ML Model Wrapper                                           │
│  • Load DistilBERT from cache/HuggingFace                  │
│  • Detect device (cuda/cpu)                                 │
│  • Tokenize text                                           │
│  • Run inference                                           │
│  • Convert logits → sentiment/score/confidence             │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Response Formatter                                         │
│  • Map model output to sentiment (positive/negative/neutral)│
│  • Calculate score (0-1)                                    │
│  • Include confidence                                       │
│  • Return JSON response                                     │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Response      │
│ {sentiment,   │
│  score,       │
│  confidence}  │
└──────────────┘
```

---

## Error Handling

### Model Loading Failures
- **Download failure** → Return 503 with "Model unavailable, retry later"
- **CUDA errors** → Log warning, fall back to CPU automatically
- **Out of memory** → Return 503 with "GPU OOM, try smaller batch"
- **Import errors** → Fail fast at startup with clear error message

### Request Failures
- **Empty text** → Return 400 with validation error
- **Text too long** → Return 400 with error
- **Model not loaded** → Return 503 with "Service initializing"
- **Inference timeout** → Cancel and return 408

### Error Response Format
```json
{
  "error": {
    "code": "MODEL_LOAD_FAILED",
    "message": "Failed to load DistilBERT model",
    "details": {
      "model": "distilbert-base-uncased-finetuned-sst-2-english",
      "cache_dir": "./models_cache"
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
- Model loader initialization (mocked model)
- Device detection (cuda/cpu fallback)
- Text preprocessing (tokenization, truncation)
- Response formatting

### Integration Tests
- End-to-end sentiment analysis with mock model
- GPU/CPU fallback behavior
- Batch processing
- API endpoint validation

### Model Tests (optional, slow)
- Verify real DistilBERT loads and generates
- Test on sample texts (positive, negative, neutral)
- Accuracy validation against known labels

### Test Requirements
- Mock model outputs for fast CI
- Real model tests marked as `@pytest.mark.slow` and optional
- Coverage target: 80%

---

## Implementation Approach

### Phase 1: Foundation (Tasks 1-3)
- Create `ml_model.py` with DistilBERT wrapper
- Update requirements.txt (uncomment torch/transformers)
- Update config.py (force USE_ML_MODEL=True, add DEVICE)

### Phase 2: Model Integration (Tasks 4-6)
- Implement model loader with hybrid GPU/CPU support
- Create model download script
- Update Dockerfile to download model during build

### Phase 3: Code Cleanup (Task 7)
- Remove all rule-based code from `sentiment_analyzer.py`
- Simplify analyze() and analyze_batch() methods
- Update main.py to require model on startup

### Phase 4: Testing & Docs (Tasks 8-10)
- Create unit tests with mocked model
- Update README.md with ML setup instructions
- Update API documentation

---

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Language** | Python 3.12+ | ARM64 compatible |
| **Framework** | FastAPI | Async support |
| **ML Framework** | PyTorch 2.1+ | ARM64/CUDA 13 compatible |
| **Model** | DistilBERT SST-2 | HuggingFace transformers |
| **Tokenization** | DistilBertTokenizer | Auto tokenizer |
| **Container** | Docker | Multi-stage ARM64 |

---

## System Specifications

**Target Platform:**
- **Architecture:** ARM64 (aarch64)
- **GPU:** NVIDIA GB10
- **CUDA:** Version 13.0
- **Driver:** 580.126.09

**Model Specifications:**
- **Name:** distilbert-base-uncased-finetuned-sst-2-english
- **Size:** ~250MB
- **Labels:** negative (0), positive (1)
- **Input:** Text, max 512 tokens
- **Output:** Sentiment classification with confidence scores

---

## Files to Modify

### Core Service (4 files)
1. `services/sentiment-agent/src/sentiment_agent/ml_model.py` - NEW: ML model wrapper
2. `services/sentiment-agent/src/sentiment_agent/sentiment_analyzer.py` - MODIFY: Remove rule-based code
3. `services/sentiment-agent/src/sentiment_agent/config.py` - MODIFY: Update model config
4. `services/sentiment-agent/requirements.txt` - MODIFY: Uncomment ML dependencies

### Scripts (1 file)
5. `scripts/download-model.sh` - NEW: Model download script for Docker

### Docker (1 file)
6. `services/sentiment-agent/Dockerfile` - MODIFY: Add model download step

### Documentation (3 files)
7. `services/sentiment-agent/README.md` - UPDATE: ML setup instructions
8. `docs/api/sentiment-agent.md` - UPDATE: ML-based API docs
9. `docs/plans/2026-03-07-sentiment-ml-integration-implementation.md` - NEW: Implementation plan

---

## Success Criteria

- [ ] Design document written (THIS)
- [ ] Design approved by user ✅
- [ ] Implementation plan created
- [ ] ml_model.py created with DistilBERT wrapper
- [ ] sentiment_analyzer.py simplified (rule-based removed)
- [ ] requirements.txt updated with ML dependencies
- [ ] Model download script created
- [ ] GPU/CPU hybrid device detection working
- [ ] Unit tests passing (80% coverage)
- [ ] Integration tests passing
- [ ] Docker build downloads model successfully
- [ ] Service runs on GB10 GPU (or CPU fallback)
- [ ] API endpoints return ML-based sentiment
- [ ] Documentation updated

---

## Future Phases (Out of Scope)

After ML model integration is complete:
- Add emotion detection (fine-tuned model)
- Add sentiment trend analysis over time
- Add confidence thresholding for filtering
- Add batch processing optimization

---

*Design Document - Project Chimera v0.5.0 - March 7, 2026*
