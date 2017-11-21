sleep 5
python3.4 manage.py migrate
gem install bundler && bundle install
python3.4 manage.py create_initial_data <<< "y"
python3.4 manage.py runserver 0.0.0.0:8000
