@echo off
call conda activate replace_with_env_name
cd /d "%~dp0"
jupyter notebook src\explore_data.ipynb
cmd /k
