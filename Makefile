help:
	@echo "Call a specific subcommand:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo

default: help

.state/docker-build-web: Dockerfile dev-requirements.txt base-requirements.txt
	# Build web container for this project
	docker compose build --force-rm web

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/docker-build-web

.state/db-migrated:
	# Call migrate target
	make migrate 

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/db-migrated

.state/db-initialized: .state/docker-build-web .state/db-migrated
	# Load all fixtures
	docker compose run --rm web ./manage.py loaddata fixtures/*.json

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/db-initialized

serve: .state/db-initialized ## Start the application
	docker compose up --remove-orphans

migrations: .state/db-initialized ## Generate migrations from models
	docker compose run --rm web ./manage.py makemigrations  
	
migrate: .state/docker-build-web ## Run Django migrate
	docker compose run --rm web ./manage.py migrate 

manage: .state/db-initialized ## Run Django manage to accept arbitrary arguments
	docker compose run --rm web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

shell: .state/db-initialized ## Open Django interactive shell
	docker compose run --rm web ./manage.py shell

clean: ## Clean up the environment
	docker compose down -v
	rm -f .state/docker-build-web .state/db-initialized .state/db-migrated 

test: .state/db-initialized ## Run tests
	docker compose run --rm web ./manage.py test

docker_shell: .state/db-initialized ## Open a bash shell in the web container
	docker compose run --rm web /bin/bash

.PHONY: help serve migrations migrate manage shell clean test docker_shell
