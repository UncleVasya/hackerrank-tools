.PHONY: manage shell migrate update_games update_bots update_matches myscript

#
# This is similar to "include ../Makefile"
# but supports target overrides.
#
%: force
	@$(MAKE) -f ../Makefile $@
force: ;

manage = python manage.py

#
# Launches website locally
#
run:
	@echo Collecting static files...
	$(manage) collectstatic --noinput

	@echo Launching website...
	$(manage) runserver

	@echo Done

#
# Launches Django shell
#
shell:
	$(manage) shell

#
# Makes and applies migrations for all apps or just APP_NAME
#
migrate:
ifndef APP
	@echo Making migrations...
	$(manage) makemigrations

	@echo Applying migrations...
	$(manage) migrate

	@echo Done
else
	@echo Making migrations for $(APP)...
	$(manage) makemigrations $(APP)

	@echo Applying migrations for $(APP)...
	$(manage) migrate $(APP)

	@echo Done
endif

#
# Updates Game list from hackerrank.com
#
update_games:
	@echo Updating Game list from hackerrank.com...
	$(manage) update_games

#
# Updates Bot list from hackerrank.com
# This also updates Player list (bot owners)
#
update_bots:
	@echo Updating Bot list from hackerrank.com...
	$(manage) update_bots --games ${games}

#
# Updates Match list from hackerrank.com
#
update_matches:
	@echo Updating Match list from hackerrank.com...
	$(manage) update_matches --limit ${limit} --backwards ${backwards} --forced ${forced}

#
# Just a place to write scripts during development
#
myscript:
	$(manage) myscript

