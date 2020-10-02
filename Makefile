runserver:
	python manage.py runserver 0.0.0.0:8000

sass:
	 cd static && sass --compass --scss -I $(dirname $(dirname $(gem which susy))) --trace --watch sass/style.scss:sass/style.css

run:
	make -j2 runserver sass
