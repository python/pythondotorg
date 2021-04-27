runserver:
	python manage.py runserver 0.0.0.0:8000

sass:
	PATH=$(shell npm bin):$(shell echo $$PATH) sass -I static/vendor/compass -I static/vendor/susy static/sass

sass-watch:
	PATH=$(shell npm bin):$(shell echo $$PATH) sass -w -I static/vendor/compass -I static/vendor/susy static/sass
