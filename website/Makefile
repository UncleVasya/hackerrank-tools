.PHONY: manage shell migrate makemigrations update_games

include ../Makefile

manage = foreman run python manage.py

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
	@echo Making migrations
	$(manage) makemigrations

	@echo Applying migrations
	$(manage) migrate

	@echo Done
else
	@echo Making migrations for $(APP_NAME)
	$(manage) makemigrations $(APP_NAME)

	@echo Applying migrations for $(APP_NAME)
	$(manage) migrate $(APP_NAME)

	@echo Done
endif

#
# Updates game list from hackerrank.com
#
update_games:
	@echo Updating game list from hackerrank.com
	$(manage) update_games

myscript:
	$(manage) myscript

