.PHONY: install install-dev install-all test lint smoke run sync sync-once sync-dry

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-all:
	pip install -r requirements-full.txt

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m ruff check src/ tests/ main.py || python3 -m py_compile main.py

smoke:
	python3 scripts/smoke_check.py

run:
	python3 -m streamlit run main.py

sync:
	python3 -m src.sal.sync_worker

sync-once:
	python3 -m src.sal.sync_worker --once

sync-dry:
	python3 -m src.sal.sync_worker --dry-run
