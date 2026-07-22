# Shortcuts for common tasks.
# All Python commands use the virtual environment in .venv/

.PHONY: setup venv api ui test tests sample-upload

# --- One-time setup: create virtual env + install packages ---
setup: venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	cp -n .env.example .env || true
	@echo ""
	@echo "Setup done!  Activate the virtual environment with:"
	@echo "  source .venv/bin/activate"

# --- Create the Python virtual environment (isolated copy of Python + packages) ---
venv:
	python3.12 -m venv .venv

# --- Start the FastAPI backend on http://localhost:8000 ---
api:
	PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload --port 8000

# --- Start the Streamlit UI on http://localhost:8501 ---
ui:
	PYTHONPATH=. STREAMLIT_BROWSER_GATHER_USAGE_STATS=false .venv/bin/streamlit run frontend/streamlit_app.py --server.headless true

# --- Run all automated tests (use: make test or make tests) ---
test tests:
	PYTHONPATH=. .venv/bin/pytest -q

# --- Quick test: upload the sample document via curl ---
sample-upload:
	curl -s -X POST http://localhost:8000/upload \
	  -F "file=@data/sample_docs/healthcare_handbook.txt" | python3 -m json.tool
