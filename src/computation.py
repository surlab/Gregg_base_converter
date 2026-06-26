"""generic description of this module, computation.py(comp).
generated automatically on project creation from the surlab python-template-repo. 
please update this docstring as you develop.

computation.py should contain functions that actually manipulate or compute on the underlying data. 
Attempts should be made to write tests for these functions - most other src functions it will be obvious in 
end to end testing if they work, however its important that the computations are tested and robust since
the shape/structure/general appearance is not suffifcient to ensure you have actually done what you think you have.
"""

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import config as cfg
from src import helper_functions as hf
#import xarray as xr
#####################################
