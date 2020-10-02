sass:
	 cd static && sass --compass --scss -I $(dirname $(dirname $(gem which susy))) --trace --watch sass/style.scss:sass/style.css
