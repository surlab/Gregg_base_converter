call ".\maintainer_scripts\replace_repo_name_in_text.bat"
timeout 5
cd maintainer_scripts
call "create_new_env_win.bat"

del "README.md"
ren "PROJECT_README.md" README.md

del ".\maintainer_scripts\replace_repo_name_in_text.bat"
call ".\maintainer_scripts\simple_WIP_commit_push_close.bat"
timeout 5
del dev_install_win.bat
