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
	foreman start web;

#
# Pushes website folder on heroku
#
deploy:
	git subtree push --prefix website heroku master
