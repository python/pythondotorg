# python.org

[![Build Status](https://travis-ci.org/python/pythondotorg.png?branch=master)](https://travis-ci.org/python/pythondotorg)
[![Documentation Status](https://readthedocs.org/projects/pythondotorg/badge/?version=latest)](http://pythondotorg.readthedocs.org/?badge=latest)

### General information

* Source code: https://github.com/python/pythondotorg
* Issue tracker: https://github.com/python/pythondotorg/issues
* Documentation: https://pythondotorg.readthedocs.org/
* Mailing list: [pydotorg-www](https://mail.python.org/mailman/listinfo/pydotorg-www)
* IRC: `#pydotorg` on Freenode
* Staging site: https://staging.python.org/ (`master` branch)
* License: Apache 2.0 License

python.org is a **Django** based web site, which uses several `applications` for different parts of site. The main entry point is the [pydotorg](https://github.com/python/pythondotorg/tree/master/pydotorg) application, which contains [root URL mapping](https://github.com/python/pythondotorg/blob/master/pydotorg/urls.py). Applications are contained in their own directories at repository root, and maintain their own URL maps (in `urls.py` file), data models (`models.py`) and view (request processing logic in `views.py`).

Jobs application relies on **specific features of PostgreSQL** database (#911). Site stylesheets are compiled using [compass](http://compass-style.org/), which in turn requires **Ruby**.

Site management is done with standard Django **manage.py** script located in the root of this repository.
