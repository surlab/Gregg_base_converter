"""generic description of this module, plotting.py(plot)
generated automatically on project creation from the surlab python-template-repo. 
please update this docstring as you develop.

plotting.py should contain functions used for plotting the results of main_computation. 
This can also include saving of plots, if its more convenient than placing in data_io
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import config as cfg
from src import helper_functions as hf

# Consider putting some common convenienve functions here? like the newfig or saving wrappers?
