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
	#Build web container for this project 
	docker-compose build --build-arg IPYTHON=$(IPYTHON) --force-rm web

	#Mark the state so we don't rebuild this needlessly.
	mkdir -p .state
	touch .state/docker-build-web


.state/db-initialized: .state/docker-build-web
	#Run Django migrations and load all fixtures 
	docker-compose run --rm web ./manage.py migrate 
	docker-compose run --rm web ./manage.py loaddata fixtures/*.json

	#Mark the state so we don't rebuild this needlessly.
	mkdir -p .state
	touch .state/db-initialized


serve: .state/db-initialized
	docker-compose up -d


clean:
	docker container rm $$(docker ps -aq) -f
	rm -f .state/*
