#!/usr/bin/env python3

# Manually tag by genre at the volume level

import csv, os, sys, random
from collections import Counter
import numpy as np
import pandas as pd

from sklearn import svm
from sklearn import cross_validation
from sklearn.preprocessing import StandardScaler

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils

bzipmeta = pd.read_csv('bzipmeta.csv', dtype = 'object', index_col = 'docid', na_filter = False)

tagged = pd.read_csv('firsttrainingset.csv', dtype = 'object', index_col = 'docid', na_filter = False)

alreadyhave = list(tagged.index)

taggedbythis = pd.read_csv('taggedvolumes.csv', dtype = 'object', index_col = 'docid', na_filter = False)

alreadyhave.extend(list(taggedbythis.index))

nottagged = bzipmeta.drop(alreadyhave)

randvector = list(nottagged.loc[nottagged['sampledas'] == 'dra', : ].index)
print(len(randvector))

random.shuffle(randvector)

taggedrows = dict()

for anid in randvector:
    print()
    thisrow = nottagged.loc[anid, : ]
    print(thisrow['author'])
    print(thisrow['genres'])
    print(thisrow['title'])
    print(thisrow['subjects'])
    user = input('Genre? ')
    if user == 'none':
        continue
    elif user == 'stop':
        break
    else:
        thisrow['volgenre'] = user
        taggedrows[anid] = thisrow

additionaldf = pd.DataFrame.from_dict(taggedrows, orient = 'index')

newandold = pd.concat([taggedbythis, additionaldf])
newandold.to_csv('taggedvolumes.csv', index_label = 'docid')



