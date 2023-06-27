@echo off

cd /D "%~dp0"

call env_offline.bat
python my_api.py -q 4 %*

pause
