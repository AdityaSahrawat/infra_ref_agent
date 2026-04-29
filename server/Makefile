PYTHON := .venv/bin/python

.PHONY: dev migrate test

dev:
	$(PYTHON) -m uvicorn app.main:app --reload

migrate:
	$(PYTHON) -m alembic upgrade head

test:
	$(PYTHON) -m pytest -q
