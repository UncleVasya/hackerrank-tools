.PHONY: run

VIRTUALENV = $(HOME)/.virtualenvs/hackerrank-tools

SHELL = /bin/bash
venv = source $(VIRTUALENV)/bin/activate

# uses Foreman to launch website locally
run:
	$(venv); \
	cd website; \
	foreman start web;

# pushes website folder on heroku
deploy:
	git subtree push --prefix website heroku master
