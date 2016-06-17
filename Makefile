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

#
# Uploads packed website folder on heroku.
# Useful when push via git has issues.
#
deploy_archive:
ifndef APP
	python website/deploy_archive.py -a hktools-staging
else
	python website/deploy_archive.py -a $(APP)
endif
