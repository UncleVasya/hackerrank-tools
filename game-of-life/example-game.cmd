REM python playgame.py --verbose --fill --log_input --log_output --log_error --log_dir game_logs --strict "bots\UncleVasya_1.x.exe" "python bots\sample_bots\RandomBot.py" --turntime 5000
REM python playgame.py --verbose --fill --log_input --log_output --log_error --log_dir game_logs --strict "python bots\sample_bots\RandomBot.py" "python bots\sample_bots\RandomBot.py" --turntime 5000
python playgame.py --verbose --fill --log_input --log_output --log_error --log_dir game_logs --strict "bots\UncleVasya_1.x.exe" "bots\UncleVasya_1.x.exe" --turntime 5000
pause