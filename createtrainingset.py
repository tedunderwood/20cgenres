#!/usr/bin/env python3

# Create training sets. This short function does nothing
# but combine confidentvolumes (created by inferfromreaders)
# and taggedvolumes (created by manualtagging).

import csv, os, sys, random
from collections import Counter
import numpy as np
import pandas as pd

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils

alreadyhave = pd.read_csv('confidentvolumes.csv', dtype = 'object', index_col = 'docid', na_filter = False)

newlytagged = pd.read_csv('taggedvolumes.csv', dtype = 'object', index_col = 'docid', na_filter = False)

both = pd.concat([alreadyhave, newlytagged])
both.to_csv('maintrainingset.csv', index_label = 'docid')
