#!/usr/bin/env python3

# crossvalidate_ensemble

# Crossvalidating an ensemble is a pain in the butt, because
# *all* the models have to be regenerated again and again.

import csv, os, sys, pickle, random
from collections import Counter
import numpy as np
import pandas as pd

from sklearn import svm
from sklearn import cross_validation
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils

import trainamodel
import implementmodel

def train_ensemble(trainingpath):

    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'fic', 'bio', 570, 0.009, 'crossmodels/ficvsbio.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'fic', '~fic', 850, 0.015, 'crossmodels/ficvsall.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'poe', '~poe', 260, 0.025, 'crossmodels/poevsall.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'dra', '~dra', 960, 0.01, 'crossmodels/dravsall.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'dra', 'poe', 1300, 0.015, 'crossmodels/dravspoe.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'fic', 'nonbio', 830, 0.002, 'crossmodels/ficvsnonbio.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'fic', 'dra', 1000, 0.01, 'crossmodels/ficvsdra.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'poe', 'nonbio', 550, 0.01, 'crossmodels/poevsnonbio.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'fic', 'poe', 60, 0.037, 'crossmodels/ficvspoe.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'poe', 'bio', 700, 0.009, 'crossmodels/poevsbio.p')
    trainamodel.export_svm_model(trainingpath, '/Volumes/TARDIS/work/train20', 'dra', 'bio', 250, 0.007, 'crossmodels/dravsbio.p')

def check_ensemble(testpath, outpath):
    implementmodel.main(sourcedir = '/Volumes/TARDIS/work/train20', metapath = testpath, modeldir = 'crossmodels/', outpath = outpath)

# MAIN SCRIPT BEGINS HERE

meta = pd.read_csv('maintrainingset.csv', index_col = 'docid', dtype = 'object')

docids = meta.index.tolist()
random.shuffle(docids)

docidct = len(docids)
chunklen = (docidct // 5) + 1

floor = 0
folds = []
for i in range(5):
    ceiling = floor + chunklen
    if ceiling > (docidct - 1):
        ceiling = docidct - 1

    folds.append(docids[floor : ceiling])

    floor = ceiling

for i in range(5):
    fold = folds[i]
    trainingdata = meta.drop(fold)
    testdata = meta.loc[fold, : ]
    trainingdata.to_csv('crossmodels/trainingdata.csv')
    testdata.to_csv('crossmodels/testdata.csv')
    train_ensemble('crossmodels/trainingdata.csv')
    print()
    print("ENSEMBLE TRAINED; now implementing.")
    print()
    outpath = 'crossmodels/predictions' + str(i) + '.csv'
    check_ensemble('crossmodels/testdata.csv', outpath)

frames = []
for i in range(5):
    inpath = 'crossmodels/predictions' + str(i) + '.csv'
    frame = pd.read_csv(inpath, index_col = 'docid', dtype = 'object')
    frames.append(frame)

wholething = pd.concat(frames)
wholething.to_csv('crossmodels/predictions.csv')




