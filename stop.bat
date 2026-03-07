@echo off
echo Stopping Telegram Anti-Bot...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq bot.py*"
echo Bot stopped!
pause
