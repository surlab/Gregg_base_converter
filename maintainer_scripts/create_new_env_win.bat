REM Creates conda environment from environment_cross_platform.yml
cd ..
conda env create -f environment_cross_platform.yml
call conda activate replace_with_env_name
call conda info --envs
