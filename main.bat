@echo off
call conda activate replace_with_env_name
cd /d "%~dp0"
python -m src.main
cmd /k
