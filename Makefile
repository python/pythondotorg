.DEFAULT_GOAL := help

help: ## Display this help text
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# =============================================================================
# Docker State
# =============================================================================

.state/docker-build-web: Dockerfile pyproject.toml
	docker compose build --force-rm web
	mkdir -p .state && touch .state/docker-build-web

.state/db-migrated:
	make migrate
	mkdir -p .state && touch .state/db-migrated

.state/db-initialized: .state/docker-build-web .state/db-migrated
	docker compose run --rm web ./manage.py createcachetable
	docker compose run --rm web ./manage.py loaddata fixtures/*.json
	mkdir -p .state && touch .state/db-initialized

# =============================================================================
# Development
# =============================================================================

##@ Development

serve: .state/db-initialized ## Start the application
	docker compose up --remove-orphans

migrations: .state/db-initialized ## Generate migrations from models
	docker compose run --rm web ./manage.py makemigrations

migrate: .state/docker-build-web ## Run Django migrate
	docker compose run --rm web ./manage.py migrate

manage: .state/db-initialized ## Run arbitrary manage.py commands
	docker compose run --rm web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

shell: .state/db-initialized ## Open Django interactive shell
	docker compose run --rm web ./manage.py shell

docker_shell: .state/db-initialized ## Open bash in web container
	docker compose run --rm web /bin/bash

clean: ## Clean up the environment
	docker compose down -v
	rm -f .state/docker-build-web .state/db-initialized .state/db-migrated

# =============================================================================
# Code Quality
# =============================================================================

##@ Code Quality

lint: ## Run ruff linter (--fix enabled)
	@if command -v ruff >/dev/null 2>&1; then ruff check --fix .; else docker compose run --rm web ruff check --fix .; fi

fmt: ## Run ruff formatter
	@if command -v ruff >/dev/null 2>&1; then ruff format .; else docker compose run --rm web ruff format .; fi

test: .state/db-initialized ## Run test suite
	docker compose run --rm web ./manage.py test

ci: lint fmt test ## Run lint, fmt, then tests

# =============================================================================
# Documentation
# =============================================================================

##@ Documentation

docs: docs-clean ## Build documentation
	@echo "=> Building documentation"
	@uv sync --group docs
	@uv run sphinx-build -M html docs/source docs/_build/ -E -a -j auto --keep-going

docs-serve: docs-clean ## Serve documentation with live reload
	@echo "=> Serving documentation"
	@uv sync --group docs
	@uv run sphinx-autobuild docs/source docs/_build/ -j auto --port 0

docs-clean: ## Clean built documentation
	@echo "=> Cleaning documentation build assets"
	@rm -rf docs/_build
	@echo "=> Removed existing documentation build assets"

# =============================================================================
# Frontend
# =============================================================================

##@ Frontend

css: ## Minify CSS with Lightning CSS
	npx lightningcss-cli --minify static/css/style.css -o static/css/style.min.css
	npx lightningcss-cli --minify static/css/mq.css -o static/css/mq.min.css

css-check: ## Validate CSS parses without errors
	npx lightningcss-cli --minify static/css/style.css -o /dev/null
	npx lightningcss-cli --minify static/css/mq.css -o /dev/null

.PHONY: help serve migrations migrate manage shell docker_shell clean
.PHONY: lint fmt test ci
.PHONY: docs docs-serve docs-clean
.PHONY: css css-check
