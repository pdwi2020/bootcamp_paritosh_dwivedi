PYTHON := .venv/bin/python

.PHONY: setup test pipeline verify

setup:
	uv venv --python 3.11 .venv
	uv pip install --python $(PYTHON) -r project/requirements.txt

test:
	$(PYTHON) -m pytest project/tests -q

pipeline:
	cd project && ../$(PYTHON) run_pipeline.py

verify:
	cd project && ../$(PYTHON) verify_project.py
