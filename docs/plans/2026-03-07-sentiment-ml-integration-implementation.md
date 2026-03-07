# Sentiment Agent ML Model Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace rule-based sentiment analysis with DistilBERT ML model for improved accuracy on ARM64 GB10 GPU

**Architecture:** ML-only sentiment service with DistilBERT SST-2 model, hybrid GPU/CPU support, model downloaded during Docker build

**Tech Stack:** Python 3.12+, FastAPI, PyTorch 2.1+ (ARM64/CUDA 13), Transformers 4.36+, DistilBERT SST-2

---

## Phase 1: Foundation Setup

### Task 1: Create ML Model Wrapper Module

**Files:**
- Create: `services/sentiment-agent/src/sentiment_agent/ml_model.py`

**Step 1: Write the ML model wrapper**

```python
"""ML Model Wrapper for Sentiment Analysis."""

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
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

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/sentiment-agent/src/sentiment_agent/ml_model.py`
Expected: No output (syntax valid)

**Step 3: Commit**

```bash
git add services/sentiment-agent/src/sentiment_agent/ml_model.py
git commit -m "feat(sentiment): add DistilBERT ML model wrapper"
```

---

### Task 2: Update Configuration

**Files:**
- Modify: `services/sentiment-agent/src/sentiment_agent/config.py`

**Step 1: Update Settings class**

Find the Settings class and update the Model Configuration section:

```python
# Model Configuration
use_ml_model: bool = True  # Forced to True for ML-only approach
model_path: Optional[str] = None  # Not used, using HuggingFace
model_cache_dir: str = "./models_cache"
device: str = "auto"  # Auto-detect cuda/cpu
```

**Step 2: Verify file**

Run: `cat services/sentiment-agent/src/sentiment_agent/config.py`
Expected: Updated configuration values

**Step 3: Commit**

```bash
git add services/sentiment-agent/src/sentiment_agent/config.py
git commit -m "feat(sentiment): update config for ML-only approach"
```

---

### Task 3: Update Requirements

**Files:**
- Modify: `services/sentiment-agent/requirements.txt`

**Step 1: Uncomment ML dependencies**

Find the ML/NLP section and uncomment:

```python
# ML/NLP
transformers==4.36.0
torch==2.1.0
```

**Step 2: Verify file**

Run: `cat services/sentiment-agent/requirements.txt`
Expected: ML dependencies uncommented

**Step 3: Commit**

```bash
git add services/sentiment-agent/requirements.txt
git commit -m "feat(sentiment): enable ML dependencies in requirements"
```

---

## Phase 2: Model Integration

### Task 4: Rewrite Sentiment Analyzer (Remove Rule-Based Code)

**Files:**
- Modify: `services/sentiment-agent/src/sentiment_agent/sentiment_analyzer.py`

**Step 1: Remove all rule-based constants and methods**

Remove the following from the file:
- Lines 21-23: Commented imports (delete or uncomment actual imports)
- Lines 34-68: All keyword constants (POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, EMOTION_KEYWORDS, INTENSITY_BOOSTERS, INTENSITY_DIMINISHERS)
- Lines 95-101: Commented `_load_ml_model` method
- Lines 148-268: `_analyze_rule_based`, `_calculate_emotions`, `_neutral_result` methods
- Lines 286-311: Commented `_analyze_with_ml` method (we have the real implementation now)

**Step 2: Update __init__ method**

```python
def __init__(self, use_ml_model: bool = True):
    """
    Initialize the sentiment analyzer.

    Args:
        use_ml_model: Must be True (ML-only approach)
    """
    if not use_ml_model:
        raise ValueError("ML-only approach: use_ml_model must be True")

    from ml_model import SentimentModel
    self.model = SentimentModel(
        cache_dir=self.settings.model_cache_dir,
        device=self.settings.device
    )
    self.model_available = False
```

**Step 3: Update analyze method**

```python
def analyze(self, text: str) -> Dict:
    """
    Analyze sentiment of a single text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with sentiment, score, confidence
    """
    if not text or not text.strip():
        return self._neutral_result()

    # Load model if not loaded
    if not self.model_available:
        self.model.load()
        self.model_available = True

    return self.model.analyze(text)
```

**Step 4: Simplify analyze_batch method**

```python
def analyze_batch(self, texts: List[str]) -> List[Dict]:
    """
    Analyze sentiment of multiple texts.

    Args:
        texts: List of texts to analyze

    Returns:
        List of sentiment analysis results
    """
    if not texts:
        return []

    # Load model if not loaded
    if not self.model_available:
        self.model.load()
        self.model_available = True

    return self.model.analyze_batch(texts)
```

**Step 5: Update _neutral_result helper**

Keep the _neutral_result method but simplify it:

```python
def _neutral_result(self) -> Dict:
    """Return a neutral sentiment result."""
    return {
        "sentiment": "neutral",
        "score": 0.5,
        "confidence": 0.5,
        "emotions": {
            "joy": 0.0,
            "surprise": 0.0,
            "neutral": 1.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0
        }
    }
```

**Step 6: Verify syntax**

Run: `python3 -m py_compile services/sentiment-agent/src/sentiment_agent/sentiment_analyzer.py`
Expected: No output

**Step 7: Commit**

```bash
git add services/sentiment-agent/src/sentiment_agent/sentiment_analyzer.py
git commit -m "refactor(sentiment): replace rule-based with ML model"
```

---

### Task 5: Update Main Application for Model Loading

**Files:**
- Modify: `services/sentiment-agent/src/sentiment_agent/main.py`

**Step 1: Update lifespan or startup to load model**

Find the startup/lifespan code and add model loading:

```python
from sentiment_analyzer import SentimentAnalyzer

# On startup
analyzer = SentimentAnalyzer()
try:
    analyzer.model.load()
    logger.info("Sentiment ML model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load ML model: {e}")
    raise  # Fail startup if model unavailable
```

**Step 2: Verify and commit**

```bash
git add services/sentiment-agent/src/sentiment_agent/main.py
git commit -m "feat(sentiment): require ML model on startup"
```

---

## Phase 3: Docker & Deployment

### Task 6: Create Model Download Script

**Files:**
- Create: `scripts/download-sentiment-model.sh`

**Step 1: Write download script**

```bash
#!/bin/bash
# Download DistilBERT model for Sentiment Agent

set -e

MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english"
CACHE_DIR="./models_cache"

echo "Downloading $MODEL_NAME..."
mkdir -p "$CACHE_DIR"

python3 << EOF
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

print(f"Downloading {MODEL_NAME}...")
tokenizer = DistilBertTokenizer.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
model = DistilBertForSequenceClassification.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
print("Download complete!")
print(f"Model cached to: $CACHE_DIR")
EOF

echo "Model download complete"
```

**Step 2: Make executable**

Run: `chmod +x scripts/download-sentiment-model.sh`

**Step 3: Commit**

```bash
git add scripts/download-sentiment-model.sh
git commit -m "feat(sentiment): add model download script"
```

---

### Task 7: Update Dockerfile

**Files:**
- Modify: `services/sentiment-agent/Dockerfile`

**Step 1: Add model download before Python copy**

Find the Python package copy section and add before it:

```dockerfile
# Download ML model (if needed during build)
RUN python3 -c "
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import os
cache_dir = './models_cache'
os.makedirs(cache_dir, exist_ok=True)
print('Downloading DistilBERT model...')
DistilBertTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english', cache_dir=cache_dir)
DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english', cache_dir=cache_dir)
print('Model downloaded successfully')
"
```

**Step 2: Verify and commit**

```bash
git add services/sentiment-agent/Dockerfile
git commit -m "feat(sentiment): download ML model during Docker build"
```

---

## Phase 4: Testing & Documentation

### Task 8: Create Unit Tests

**Files:**
- Create: `services/sentiment-agent/tests/test_ml_model.py`

**Step 1: Write ML model tests**

```python
"""Unit tests for ML model wrapper."""

import pytest
from unittest.mock import Mock, patch
import torch

from src.sentiment_agent.ml_model import SentimentModel


class TestSentimentModel:
    """Test SentimentModel class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache_dir = "./test_cache"

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_init_creates_instance(self, mock_model_class, mock_tokenizer_class):
        """Test initialization creates instance."""
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")

        assert model.cache_dir == self.cache_dir
        assert model.device == "cpu"
        assert model.model is None

    def test_detect_device_cuda_available(self):
        """Test CUDA device detection when available."""
        with patch('torch.cuda.is_available', return_value=True):
            model = SentimentModel(device="auto")
            assert model.device == "cuda"

    def test_detect_device_cpu_fallback(self):
        """Test CPU fallback when CUDA unavailable."""
        with patch('torch.cuda.is_available', return_value=False):
            model = SentimentModel(device="auto")
            assert model.device == "cpu"

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_load_model(self, mock_model_class, mock_tokenizer_class):
        """Test model loading."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.load()

        assert model.model is not None
        assert model.tokenizer is not None

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_analyze_returns_sentiment(self, mock_model_class, mock_tokenizer_class):
        """Test analyze returns sentiment dict."""
        # Setup mock model
        mock_model = Mock()
        mock_tokenizer = Mock()

        # Mock model output (positive sentiment)
        mock_output = Mock()
        mock_output.logits = torch.tensor([[1.0, 5.0]])  # High positive logit
        mock_model.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock tokenizer
        mock_inputs = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.model = mock_model
        model.tokenizer = mock_tokenizer

        result = model.analyze("This is amazing!")

        assert "sentiment" in result
        assert "score" in result
        assert "confidence" in result
```

**Step 2: Verify and commit**

```bash
git add services/sentiment-agent/tests/test_ml_model.py
git commit -m "test(sentiment): add ML model unit tests"
```

---

### Task 9: Update README Documentation

**Files:**
- Modify: `services/sentiment-agent/README.md`

**Step 1: Update Quick Start section**

Replace the ML model mention:

```markdown
## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - DistilBERT model (~250MB, auto-downloaded)

# Local development setup
cd services/sentiment-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env if needed (default: auto-detect cuda/cpu)

# Run service
uvicorn main:app --reload --port 8004
```

**Model Information:**

The service uses **DistilBERT fine-tuned on SST-2** for sentiment analysis:
- **Model:** `distilbert-base-uncased-finetuned-sst-2-english`
- **Size:** ~250MB
- **Labels:** Negative (0), Positive (1)
- **Auto-downloaded:** On first run or during Docker build
- **Device:** Auto-detects GPU (CUDA) or CPU
```

**Step 2: Update Troubleshooting section**

Add/replace model-related troubleshooting:

```markdown
## Troubleshooting

### Model Download Failed
**Symptom:** Service fails to start with model import error
**Solution:** Ensure internet connectivity for first run, or build Docker image with network access

### CUDA Out of Memory
**Symptom:** Service crashes with CUDA OOM error
**Solution:** Set `DEVICE=cpu` in .env to use CPU instead

### Slow Inference
**Symptom:** Analysis takes >1 second per request
**Solution:** Ensure GPU is being used (check logs for device detection)
```

**Step 3: Verify and commit**

```bash
git add services/sentiment-agent/README.md
git commit -m "docs(sentiment): update README for ML model approach"
```

---

### Task 10: Update API Documentation

**Files:**
- Modify: `docs/api/sentiment-agent.md`

**Step 1: Update model configuration section**

Find the configuration table and update:

```markdown
| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ML_MODEL` | `true` | Must be true (ML-only approach) |
| `MODEL_CACHE_DIR` | `./models_cache` | HuggingFace cache directory |
| `DEVICE` | `auto` | Device: auto, cuda, or cpu |
```

**Step 2: Update response example:

```markdown
**Response:**
```json
{
  "sentiment": "positive",
  "score": 0.87,
  "confidence": 0.92
}
```

Note: Emotions are now calculated from the ML model's confidence scores rather than keyword matching.
```

**Step 3: Verify and commit**

```bash
git add docs/api/sentiment-agent.md
git commit -m "docs(api): update sentiment API docs for ML model"
```

---

## Success Criteria Verification

Run this final checklist:

```bash
echo "=== Sentiment ML Integration Checklist ==="
echo ""
echo "1. ML Model Wrapper:"
[ -f "services/sentiment-agent/src/sentiment_agent/ml_model.py" ] && echo "   ✓ ml_model.py created" || echo "   ✗ Missing"
echo ""
echo "2. Configuration Updated:"
grep -q "use_ml_model: bool = True" services/sentiment-agent/src/sentiment_agent/config.py && echo "   ✓ use_ml_model=True" || echo "   ✗ Not set"
echo ""
echo "3. Requirements Updated:"
grep -q "transformers" services/sentiment-agent/requirements.txt && echo "   ✓ transformers enabled" || echo "   ✗ Missing"
echo ""
echo "4. Rule-Based Code Removed:"
grep -q "POSITIVE_KEYWORDS" services/sentiment-agent/src/sentiment_agent/sentiment_analyzer.py && echo "   ✗ Old code still present" || echo "   ✓ Rule-based removed"
echo ""
echo "5. Model Download Script:"
[ -f "scripts/download-sentiment-model.sh" ] && echo "   ✓ Download script exists" || echo "   ✗ Missing"
echo ""
echo "6. Tests Created:"
[ -f "services/sentiment-agent/tests/test_ml_model.py" ] && echo "   ✓ Tests exist" || echo "   ✗ Missing"
echo ""
echo "7. Documentation Updated:"
grep -q "DistilBERT" services/sentiment-agent/README.md && echo "   ✓ README updated" || echo "   ✗ Not updated"
grep -q "DistilBERT" docs/api/sentiment-agent.md && echo "   ✓ API docs updated" || echo "   ✗ Not updated"
echo ""
echo "=== Verification Complete ==="
```

---

*Implementation Plan - Sentiment Agent ML Model Integration - March 7, 2026*
