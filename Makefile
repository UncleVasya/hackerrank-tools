.PHONY: run deploy

SHELL = /bin/bash

PROJECT_NAME = hackerrank-tools
VIRTUALENV = $(HOME)/.virtualenvs/$(PROJECT_NAME)

venv = source $(VIRTUALENV)/bin/activate

#
# Launches website locally with Foreman
#
run:
	$(venv); \
	cd website; \
	python manage.py collectstatic --noinput; \
	python manage.py runserver

#
# Pushes project on OpenShift
#
deploy:
	git push openshift HEAD:master

