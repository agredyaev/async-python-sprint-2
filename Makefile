ONESHELL:

.PHONY: env
env:
	@find . -name ".env.example" | while read file; do \
		cp "$$file" "$$(dirname $$file)/.env"; \
	done


.PHONY: sync
sync:
	@uv sync --frozen --all-extras

.PHONY: setup
setup:
	@curl -LsSf https://astral.sh/uv/install.sh | sh

.PHONY: upd_hooks
upd_hooks:
	@pre-commit clean
	@pre-commit install --install-hooks

.PHONY: check
check:
	@git add .
	@pre-commit run

.PHONY: up
up: env setup sync

.PHONY: run
run: sync env
	@python -m src.main

.PHONY: test
test:
	pytest
