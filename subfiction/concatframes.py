# concatframes.py

import csv, os, sys, random, glob
from collections import Counter
import numpy as np
import pandas as pd

framepaths = glob.glob('fic*.csv')
allframes = []
for path in framepaths:
    thisframe = pd.read_csv(path, index_col = 'docid', dtype = 'object')
    allframes.append(thisframe)

masterframe = pd.concat(allframes)

masterframe.loc[ : , 'nonficprob'] = pd.to_numeric(masterframe.loc[ : , 'nonficprob'], errors = 'coerce')

masterframe = masterframe.sort_values('nonficprob')

masterframe.to_csv('annotatedfiction.csv')
