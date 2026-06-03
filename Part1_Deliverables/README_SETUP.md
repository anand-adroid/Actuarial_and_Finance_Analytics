# LTC Expected Loss — Part 1: Setup & Run Instructions

This folder contains the Part 1 predictive-modelling solution. Follow the steps
below to create an isolated virtual environment, install the exact package
versions, and run the notebook end-to-end.

## Files
| File | What it is |
|------|------------|
| `LTC_Part1_Model.ipynb` | The notebook to run (full settings). |
| `LTC_Part1_Model_executed.ipynb` | A pre-run copy with outputs already embedded (lighter settings, for quick viewing). |
| `LTC_Part1_Methodology.docx / .pdf` | Written methodology & results (submission). |
| `LTC_Part1_Learning_Guide.docx / .pdf` | Plain-English explainer of every decision. |
| `requirements.txt` | Pinned package versions. |
| `ltc_actuarial_take_home_dataset.csv` | **Place the dataset here** (same folder as the notebook). |

## Prerequisites
- Python **3.10 or 3.11** installed. Check with: `python --version`

## 1. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
cd path\to\Part1_Deliverables
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks activation, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`)*

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
cd path/to/Part1_Deliverables
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install the packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Make sure the dataset is in place
Copy `ltc_actuarial_take_home_dataset.csv` into this folder (the notebook loads
it by relative path). To use a different location, edit the `pd.read_csv(...)`
line in the first data cell.

## 4. Run the notebook

**Option A — Jupyter in the browser:**
```bash
jupyter lab        # or: jupyter notebook
```
Open `LTC_Part1_Model.ipynb`, then **Run → Run All Cells**.

**Option B — VS Code:** open the `.ipynb`, and when prompted select the
`.venv` interpreter as the kernel, then **Run All**.

**Option C — run headless from the terminal:**
```bash
jupyter nbconvert --to notebook --execute LTC_Part1_Model.ipynb --output run_output.ipynb
```

## Notes
- The Optuna tuning cell takes ~30–60s. To make it faster, lower `n_trials`
  in the tuning cell (e.g. `n_trials=8`); results are stable.
- `xgboost` is listed as optional. If it fails to install on your platform you
  can remove that line — the notebook runs on LightGBM and does not import xgboost.
- Everything is seeded (`SEED = 42`) so results are reproducible.

## Common "Run All" errors
| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'lightgbm'` (etc.) | The venv isn't active or `pip install -r requirements.txt` wasn't run. Re-activate and reinstall. |
| `FileNotFoundError: ltc_actuarial_take_home_dataset.csv` | Put the CSV in this folder, or fix the path in the data cell. |
| Kernel not using the venv | In Jupyter/VS Code, select the `.venv` kernel/interpreter. |
