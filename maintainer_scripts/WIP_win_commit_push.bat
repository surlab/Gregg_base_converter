REM comment: This script runs a few housekeeping functions before committing and pushing
call update_env_yml.bay
call black src
call black scripts
REM Optional: sync notebook if jupytext is installed
REM call jupytext --sync src\explore_data.ipynb
call git add --all
call git commit -m "WIP: unstable code committed and pushed by shortcut script"
call git push
cmd /k
