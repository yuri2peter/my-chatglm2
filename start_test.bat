@echo off

cd /D "%~dp0"

call env_offline.bat

echo Start test.py
python test.py %*

pause
