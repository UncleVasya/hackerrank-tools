.PHONY: manage shell migrate update_games update_bots update_matches myscript

#
# This is similar to "include ../Makefile"
# but supports target overrides.
#
%: force
	@$(MAKE) -f ../Makefile $@
force: ;

manage = foreman run python manage.py

#
# Launches website locally with Foreman
#
run:
	@echo Collecting static files...
	$(manage) collectstatic --noinput

	@echo Launching website with Foreman...
	foreman start web

	@echo Done

#
# Executes manage command with Foreman
#
manage:
ifndef CMD
	@echo Please, specify CMD=command argument to execute
else
	$(manage) $(CMD)
endif

#
# Launches Django shell
#
shell:
	$(manage) shell

#
# Makes and applies migrations for all apps or just APP_NAME
#
migrate:
ifndef APP_NAME
	@echo Making migrations...
	$(manage) makemigrations

	@echo Applying migrations...
	$(manage) migrate

	@echo Done
else
	@echo Making migrations for $(APP_NAME)...
	$(manage) makemigrations $(APP_NAME)

	@echo Applying migrations for $(APP_NAME)...
	$(manage) migrate $(APP_NAME)

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

myscript:
	$(manage) myscript

