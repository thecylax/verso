# Execução local, sem Docker: API com SQLite (apps/api/verso.db) e front no Vite.
# No Windows as receitas rodam em PowerShell; em Linux/macOS, no sh.

API_DIR := apps/api
WEB_DIR := apps/web

# Python 3.12+ para criar a venv; troque com: make install PYTHON="py -3.12"
ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command
PYTHON ?= py -3.14
VENV_BIN := ./.venv/Scripts
MAKE_VENV = if (-not (Test-Path .venv)) { $(PYTHON) -m venv .venv }
RESET_DB := Get-ChildItem verso.db* | Remove-Item -Force
else
PYTHON ?= python3
VENV_BIN := ./.venv/bin
MAKE_VENV = [ -d .venv ] || $(PYTHON) -m venv .venv
RESET_DB := rm -f verso.db verso.db-shm verso.db-wal
endif

.DEFAULT_GOAL := help
.PHONY: help install install-api install-web check-node migrate dev api web test test-api test-web reset-db

help:
	@echo "make install    cria a venv da API e instala as dependencias do front"
	@echo "make dev        migra o SQLite e sobe API (:8000) e front (:5173) juntos"
	@echo "make api        so a API, com reload"
	@echo "make web        so o front"
	@echo "make migrate    alembic upgrade head no SQLite"
	@echo "make test       pytest (SQLite temporario) e vitest"
	@echo "make reset-db   APAGA apps/api/verso.db (todas as contas e notas locais)"

install: install-api install-web

install-api:
	cd $(API_DIR); $(MAKE_VENV)
	cd $(API_DIR); $(VENV_BIN)/python -m pip install -e ".[dev]"

install-web: check-node
	cd $(WEB_DIR); corepack enable
	cd $(WEB_DIR); pnpm install

check-node:
	node $(WEB_DIR)/scripts/check-node.mjs

migrate:
	cd $(API_DIR); $(VENV_BIN)/alembic upgrade head

api: migrate
	cd $(API_DIR); $(VENV_BIN)/uvicorn app.main:app --reload --port 8000

web: check-node
	cd $(WEB_DIR); pnpm dev

dev:
	$(MAKE) -j 2 api web

test: test-api test-web

test-api:
	cd $(API_DIR); $(VENV_BIN)/python -m pytest -q

test-web: check-node
	cd $(WEB_DIR); pnpm test

reset-db:
	cd $(API_DIR); $(RESET_DB)
