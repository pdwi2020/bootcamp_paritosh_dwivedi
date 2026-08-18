PYTHON := ../.venv/bin/python

.PHONY: lock setup format lint test pipeline notebooks presentation verify

lock:
	uv pip compile --python-version 3.11 --generate-hashes requirements.txt -o requirements.lock.txt

setup:
	uv venv --python 3.11 ../.venv
	uv pip install --python $(PYTHON) -r requirements.lock.txt

format:
	$(PYTHON) -m ruff format .

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest tests -q

pipeline:
	$(PYTHON) run_pipeline.py

notebooks:
	$(PYTHON) notebooks/build_notebooks.py
	$(PYTHON) -m ruff format notebooks
	$(PYTHON) -m ipykernel install --prefix ../tmp/jupyter-kernel --name bootcamp-venv --display-name "Bootcamp project (.venv)"
	JUPYTER_PATH="$(CURDIR)/../tmp/jupyter-kernel/share/jupyter" $(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 --ExecutePreprocessor.kernel_name=bootcamp-venv notebooks/python_fundamentals_summary.ipynb notebooks/project_pipeline.ipynb

presentation:
	$(PYTHON) build_presentation.py

verify:
	$(PYTHON) verify_project.py
