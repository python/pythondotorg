PATH  := $(shell npm bin):$(shell echo $$PATH)


runserver:
	python manage.py runserver 0.0.0.0:8000

sass:
	sass -I static/vendor/compass -I static/vendor/susy static/sass

sass-watch:
	sass -w -I static/vendor/compass -I static/vendor/susy static/sass
