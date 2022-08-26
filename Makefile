default: 
	@echo "Call a specific subcommand:"
	@echo
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null\
        | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}'\
        | sort\
        | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
	@echo
	@exit 1

.state/docker-build-web: Dockerfile dev-requirements.txt base-requirements.txt
	# Build web container for this project
	docker-compose build --force-rm web

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/docker-build-web

.state/db-migrated:
	# Call migrate target
	make migrate 

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/db-migrated

.state/db-initialized: .state/docker-build-web .state/db-migrated
	# Load all fixtures
	docker-compose run --rm web ./manage.py loaddata fixtures/*.json

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state && touch .state/db-initialized

serve: .state/db-initialized
	docker-compose up --remove-orphans

migrations: .state/db-initialized 
	# Run Django makemigrations
	docker-compose run --rm web ./manage.py makemigrations  
	
migrate: .state/docker-build-web
	# Run Django migrate
	docker-compose run --rm web ./manage.py migrate 

manage: .state/db-initialized
	# Run Django manage to accept arbitrary arguments
	docker-compose run --rm web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

shell: .state/db-initialized 
	docker-compose run --rm web ./manage.py shell

clean:
	docker-compose down -v
	rm -f .state/docker-build-web .state/db-initialized .state/db-migrated 
