@echo off

cd /D "%~dp0"

call env_offline.bat

echo Start openai_api.py
python openai_api.py %*

pause
