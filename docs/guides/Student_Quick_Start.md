# Student Quick Start Guide - Project Chimera

**Version:** 2.0.0
**Last Updated:** April 2026
**Target Audience:** New students joining Project Chimera Active Demonstrator Phase

---

## Welcome to Project Chimera,

Project Chimera is an incredibly dynamic theatre platform designed to process audience sentiment and generate adaptive responses in real-time. We have stripped away the massive scaling architecture so that **you** can focus entirely on prototyping new, bleeding-edge AI interactions!

### 🚀 Exactly How to Start immediately

You do not need to install complicated Python ML dependencies. We have prepared an optimized Docker container that builds the entire monolithic dashboard for you.

#### Step 1: Clone and Enter the Codebase
```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

#### Step 2: Spin Up the Visual Dashboard
```bash
docker compose -f docker-compose.student.yml up --build
```
*Note: The first time you run this, it will take 5-10 minutes to download the HuggingFace Machine Learning Models cleanly into the container!*

#### Step 3: View Your Hardware
Open your local web browser and successfully navigate to:
**[http://localhost:8080](http://localhost:8080)**

---

## 🎯 Student Focus Areas

To prevent students from constantly overwriting each other's code on GitHub, the project has been carefully partitioned into **three distinct functional areas**. You will be assigned one of these areas for next week's discussion!

### Focus Area 1: AI & Prompt Engineering
You are the **Brains** of the operation. Your job is to drastically improve how smart the AI feels.
- **Where you live in the code:** `services/operator-console/chimera_core.py`
- **What to fix:** Focus entirely on `generate_response()` and `select_strategy()`. Can you make the `distilgpt2` model generate scarier text for negative inputs? Can you improve the fast `heuristic_sentiment` parser to recognize sarcasm?
- **Testing:** `python chimera_core.py demo`

### Focus Area 2: Full-Stack Web App & UX
You are the **Face** of the operation. Your job is to make the audience say "Wow" when they see the dashboard.
- **Where you live in the code:** `services/operator-console/chimera_web.py` and the `static/` directory.
- **What to fix:** Our Glassmorphism CSS looks cool, but it's basic. Your job is to extract the Vanilla CSS into powerful external stylesheets, refine the `<script>` event polling to instantly flash background colors when sentiment goes red, and perhaps build an "Avatar" placeholder container on the UI.
- **Testing:** View changes live on `localhost:8080`.

### Focus Area 3: DevOps & Reliability Analytics
You are the **Shield** of the operation. Your job is to make sure your peers don't break the code, and map out the data we capture.
- **Where you live in the code:** `tests/e2e/test_chimera_smoke.py` and CSV Export logic.
- **What to fix:** Expand our active Pytest matrix so that new features pushed by Student 1 and 2 don't break the main branch. Furthermore, the `chimera_export.csv` feature drops raw data—can you build a Python script inside `scripts/` to beautifully summarize those exported CSVs into an analytics chart?
- **Testing:** `pytest tests/e2e/test_chimera_smoke.py -v`

---

## 🛠️ Testing Your Changes

Once you build the container the first time (`docker compose up`), you don't want to constantly rebuild to test minor changes!

If you are modifying pure python files locally and want to test them rapidly without Docker, use the integrated `Makefile`:

```bash
# Set up a local test environment natively
cd services/operator-console
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the local unit tests
pytest ../../tests/unit/test_chimera_core.py -v
```

Have fun hacking Project Chimera!
