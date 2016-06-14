#!/usr/bin/env python3

# trainamodel.py

# Given two categories

import csv, os, sys
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

def get_metadata(metapath, positivelabel, negativelabel):
    ''' Returns the metadata as a pandas dataframe, and lists of positive and negative
    instance IDs.
    '''
    meta = pd.read_csv(metapath, index_col = 'docid', dtype = 'object')
    positiveIDs = meta.loc[meta['volgenre'] == positivelabel, : ].index.tolist()

    # The negative label can come in two types. Either a straightforward label for
    # a specific class, or "everything but X," which takes the form of e.g. "~fic"

    if not negativelabel.startswith('~'):
        negativeIDs = meta.loc[meta['volgenre'] == negativelabel, : ].index.tolist()
    elif negativelabel.startswith('~'):
        strippedlabel = negativelabel.replace('~', '')
        negativeIDs = meta.loc[meta['volgenre'] != strippedlabel, : ].index.tolist()

    # Let's now limit metadata to volumes that are relevant to this model.
    allIDs = positiveIDs + negativeIDs
    meta = meta.loc[allIDs, : ]

    # and let's add a column to the metadata indicating whether these volumes
    # are in the positive or negative class
    classcolumn = pd.Series(np.zeros(len(allIDs)), index = allIDs)
    classcolumn.loc[positiveIDs] = 1
    meta.loc[ : , 'class'] = classcolumn

    return meta, positiveIDs, negativeIDs

def get_vocabulary(metadata, positiveIDs, negativeIDs, sourcedir, n):
    ''' Gets the top n words by docfrequency in positiveIDs + negativeIDs.
    '''

    allIDs = positiveIDs + negativeIDs

    doc_freq = Counter()

    for docid in allIDs:
        path = os.path.join(sourcedir, utils.clean_pairtree(docid) + '.csv')
        with open(path, encoding = 'utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_freq[row['feature']] += 1

    vocab = [x[0] for x in doc_freq.most_common(n)]
    print('Vocabulary constructed.')

    return vocab

def get_featureframe(vocabulary, positiveIDs, negativeIDs, sourcedir):
    ''' Returns a pandas dataframe with feature counts for all the volumes
    to be used in this model.
    '''

    df = dict()
    # We initially construct the data frame as a dictionary of Series.
    vocabset = set(vocabulary)
    allIDs = positiveIDs + negativeIDs

    for v in vocabulary:
        df[v] = pd.Series(np.zeros(len(allIDs)), index = allIDs)

    for docid in allIDs:
        path = os.path.join(sourcedir, utils.clean_pairtree(docid) + '.csv')
        with open(path, encoding = 'utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                feature = row['feature']
                if feature in vocabset:
                    df[feature].loc[docid] = row['count']

    # Now let's refashion the dictionary as an actual dataframe.
    df = pd.DataFrame(df, index = allIDs)
    df = df[vocabulary]
    # This reorders the columns to be in vocab order

    stdscaler = StandardScaler()
    scaleddf = pd.DataFrame(stdscaler.fit_transform(df), index = allIDs)

    return scaleddf

def break_into_folds(positive, negative, k):
    ''' Breaks the positive and negative sets into k stratified
    folds containing equal numbers of pos and neg instances. These
    are embodied as lists of IDs.
    '''

    folds = []

    posfloor = 0
    negfloor = 0
    for divisor in range(1, k + 1):
        pctceiling = divisor / k
        intposceiling = int(pctceiling * len(positive))
        intnegceiling = int(pctceiling * len(negative))
        postest = positive[posfloor : intposceiling]
        negtest = negative[negfloor : intnegceiling]
        test = postest + negtest
        folds.append(test)
        posfloor = intposceiling
        negfloor = intnegceiling

    return folds

def svm_model_one_fold(metadata, fold, scaleddf, c, featurecount):
    ''' This constitutes a training set by excluding volumes in fold,
    constitutes a training set that *is* fold, and then fits a linear
    SVM using parameter c. You can also specify a reduced subset of
    features, if desired; this becomes useful when we're tuning
    and trying to identify the size of an optimal feature set.
    '''

    data = scaleddf.drop(fold)
    testdata = scaleddf.loc[fold, : ]
    trainingyvals = metadata.loc[~metadata.index.isin(fold), 'class']
    realyvals = metadata.loc[fold, 'class']

    supportvector = svm.LinearSVC(C = c)
    supportvector.fit(data.loc[ : , 0: featurecount], trainingyvals)

    prediction = supportvector.predict(testdata.loc[ : , 0: featurecount])

    return prediction, realyvals

def calculate_accuracy(prediction, realyvals):
    assert len(prediction) == len(realyvals)

    actualpositives = realyvals == 1
    predictedpositives = prediction == 1
    actualnegatives = realyvals != 1
    predictednegatives = prediction != 1

    trueposct = sum(actualpositives & predictedpositives)
    truenegct = sum(actualnegatives & predictednegatives)
    falseposct = sum(actualnegatives & predictedpositives)
    falsenegct = sum(actualpositives & predictednegatives)

    assert len(realyvals) == trueposct + truenegct + falsenegct + falseposct

    accuracy = (trueposct + truenegct) / len(realyvals)
    precision = trueposct / (trueposct + falseposct)
    recall = trueposct / (trueposct + falsenegct)

    return accuracy, precision, recall

def cross_validate_svm(metadata, positiveIDs, negativeIDs, scaleddf, c, k, featurecount):
    ''' K-fold cross-validation of the model, using parameter c, and features
    up to featurecount.
    '''

    folds = break_into_folds(positiveIDs, negativeIDs, k)

    allrealclasslabels = []
    allpredictions = []
    allfolds = []

    for fold in folds:

        prediction, realclasslabels = svm_model_one_fold(metadata, fold, scaleddf, c, featurecount)
        allrealclasslabels.extend(realclasslabels)
        allpredictions.extend(prediction)
        allfolds.extend(fold)

    # The point of constructing allfolds is to reconstitute a list of IDs *in the same
    # order as* the predictions and real class labels, so it can be used to index them.

    allpredictions = pd.Series(allpredictions, index = allfolds)
    allrealclasslabels = pd.Series(allrealclasslabels, index = allfolds)

    accuracy, precision, recall = calculate_accuracy(allpredictions, allrealclasslabels)

    return accuracy, precision, recall, allpredictions, allrealclasslabels

def basic_cross_validation(metapath, sourcedir, positivelabel, negativelabel, n, k, c):

    metadata, positiveIDs, negativeIDs = get_metadata(metapath, positivelabel, negativelabel)
    vocabulary = get_vocabulary(metadata, positiveIDs, negativeIDs, sourcedir, n)
    scaleddf = get_featureframe(vocabulary, positiveIDs, negativeIDs, sourcedir)
    accuracy, precision, recall, predictions, reallabels = cross_validate_svm(metadata, positiveIDs, negativeIDs, scaleddf, c, k, n)

    print()
    print("Modeling " + positivelabel + " against " + negativelabel)
    print(accuracy, precision, recall)

    return predictions, reallabels

if __name__ == '__main__':

    ficpredicts, ficlabels = basic_cross_validation('maintrainingset.csv', '/Volumes/TARDIS/work/train20', 'fic', '~fic', 800, 5, 0.2)

    meta = pd.read_csv('maintrainingset.csv', index_col = 'docid', dtype = 'object')

    classpredicts = dict()
    classestocheck = ['bio', 'poe', 'dra']

    classpredicts['bio'], biolabels = basic_cross_validation('maintrainingset.csv', '/Volumes/TARDIS/work/train20', 'bio', 'fic', 800, 5, 0.2)

    classpredicts['poe'], poelabels = basic_cross_validation('maintrainingset.csv', '/Volumes/TARDIS/work/train20', 'poe', 'fic', 800, 5, 0.2)

    classpredicts['dra'], dralabels = basic_cross_validation('maintrainingset.csv', '/Volumes/TARDIS/work/train20', 'dra', 'fic', 800, 5, 0.2)

    toflip = []
    for idx, value in ficpredicts.iteritems():
        for g in classestocheck:
            if value > 0.5 and meta.loc[idx, 'sampledas'] == g:
                if idx in classpredicts[g] and classpredicts[g].loc[idx] > 0.5:
                    toflip.append(idx)
                elif idx not in classpredicts[g]:
                    print(idx)

    ficpredicts.loc[toflip] = 0

    accuracy, precision, recall = calculate_accuracy(ficpredicts, ficlabels)
    print()
    print('After checking volumes where metadata encouraged us to doubt: ')
    print(accuracy, precision, recall)









