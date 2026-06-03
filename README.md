# LTC Actuarial & Finance Analytics

A two-part solution for the Long-Term Care portfolio.

- **`Part1_Deliverables/`** — a predictive model for **Expected Loss (Pure Premium)** using a
  frequency × severity decomposition, with full EDA, cross-validation, calibration and fairness checks.
- **`Part2_Deliverables/`** — a runnable **GenAI tool** that ingests the model outputs, financial
  statements and macro data, retrieves governed documents with RAG, and auto-generates a
  branded **Valuation & Solvency Report** — with guardrails that guarantee every number traces to source.


## Part 1 — quickstart
```bash
cd Part1_Deliverables
python -m venv .venv            # Python 3.11 recommended
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook LTC_Part1_Model.ipynb   # Run All
```

## Part 2 — quickstart
```bash
cd Part2_Deliverables/genai_report_tool
python -m venv .venv_part2
# Windows: .\.venv_part2\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # add your OPENAI_API_KEY
python run.py --eval            # build stores -> report (Word) -> guardrail audit -> eval
# offline (no key/torch): python run.py --backend mock --embedder tfidf --eval
```
See `Part2_Deliverables/genai_report_tool/README.md` for the full design and how it scales to Azure.
