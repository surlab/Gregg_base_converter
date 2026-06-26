"""generic description of this module, helper_functions.py(hf).
generated automatically on project creation from the surlab python-template-repo. 
please update this docstring as you develop.

helper_functions.py should contain functions that are used in the other src files (computation.py, plotting.py) 
but avoids putting them in config.py where it might be confusing if they are not intended to be changed by the end user 
these are often functions that are used repeadedly to save a few lines of code, 
improve forward/backward comaptibility (e.g. retrieving somethign from the data structure)
or functions that change the structure or organization but don't change or compute on the underlying data itself
each other module should import helper_functions as hf
"""

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import config as cfg

