#!/usr/bin/env python3

# As the first stage of constructing a genre model, this
# uses tags from undergraduate readers to confirm genre tags
# for a set of 300-odd volumes.

# Initially, it produced three different kinds of output, a list
# of "confidentvolumes" where reader's judgment about the majority
# of pages echoed our initial prediction, a list of "errors" where
# those diverged, and a list of "dividedvolumes" where there was
# no clear majority of page genres.

# On closer examination, we became confident about the supposed
# "errors," and moved those into "confident," trusting the reader's
# judgment.

import csv, os, sys
from collections import Counter
import numpy as np
import pandas as pd

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils

readers = ['donofrio', 'erickson', 'alvarez', 'flynn', 'rubio', 'barajas', 'koh', 'trondson', 'lin', 'buck', 'fleming']

sourcedir = '/Volumes/TARDIS/work/readers/'

subobjects = os.listdir(sourcedir)

subdirs = [x for x in subobjects if os.path.isdir(os.path.join(sourcedir, x))]
tagset = set()
taglist = []

paths = dict()
readerowners = dict()

for subdir in subdirs:
    thisreader = 'none'
    for reader in readers:
        if reader in subdir.lower():
            thisreader = reader
            break
    if thisreader == 'none':
        print(subdir + ' lacks a recognized reader.')
        sys.exit(0)

    wholepath = os.path.join(sourcedir, subdir, 'tags')
    if os.path.isdir(wholepath):
        tagfiles = [x for x in os.listdir(wholepath) if x.endswith('.csv')]
        for f in tagfiles:
            thispath = os.path.join(wholepath, f)
            okaytoadd = True
            with open(thispath, encoding = 'utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'tag' not in row or len(row['tag']) < 3:
                        okaytoadd = False
                        break

            if okaytoadd:
                tagset.add(f)
                if f not in readerowners:
                    readerowners[f] = []
                    paths[f] = []

                if thisreader not in readerowners[f]:
                    readerowners[f].append(thisreader)
                    paths[f].append(thispath)

print(len(tagset))

allfiles = tagset
# This is a list of all the filenames (note, filenames not docids)
# that we found in the /readers sourcedir.

train1 = pd.read_csv('bzipmeta.csv', dtype = 'object', index_col = 'docid')

tidx = set(train1.index.values)
for filename in allfiles:
    docid = filename.replace('.csv', '')
    if utils.dirty_pairtree(docid) not in tidx:
        print(docid)

genrestocheck = ['fic', 'poe', 'dra', 'bio', 'non']
equivalences = {'non', 'bio', 'other'}

volumesingenre = dict()
for g in genrestocheck:
    volumesingenre[g] = []
alldocids = set()

errorconditions = dict()
erroramounts = dict()
errorids = []
percentagesbydoc = dict()

for filename, owners in readerowners.items():
    path = paths[filename][0]
    if 'metadat' in filename:
        print(filename)
        continue
    docid = utils.dirty_pairtree(filename.replace('.csv', ''))
    alldocids.add(docid)
    expectedgenre = train1.loc[docid, 'sampledas']
    with open(path, encoding = 'utf-8') as f:
        reader = csv.DictReader(f)
        genrectr = Counter()
        allct = 0
        for row in reader:
            allct += 1
            genrectr[row['tag'].lower()] += 1

    genrectr['all'] = allct

    for g in genrestocheck:
        thisgenrepct = genrectr[g] / allct
        nongenre = 0
        for g1 in equivalences:
            nongenre += genrectr[g1]
        nongenrepct = nongenre / allct
        if g == expectedgenre and thisgenrepct > 0.6:
            volumesingenre[g].append(docid)
            alldocids.remove(docid)
            break
        elif g in equivalences and expectedgenre in equivalences and nongenrepct > 0.6:
            if genrectr['bio'] > genrectr['non']:
                volumesingenre['bio'].append(docid)
            else:
                volumesingenre['non'].append(docid)
            # Here it becomes important that bio precedes non in genrestocheck
            # that way bio will always get placed in bio if possible; this is just
            # a fallback
            alldocids.remove(docid)
            break
        elif g != expectedgenre and thisgenrepct > 0.6:
            # In this case, we initially created a list of "errors" to see what we were
            # getting. But the readers seemed to be reliable, so we are recategorizing
            # the "errors" as valid genre categories.

            # errorconditions[docid] = g
            # erroramounts[docid] = thisgenrepct
            alldocids.remove(docid)
            volumesingenre[g].append(docid)
            break

    percentagesbydoc[docid] = genrectr

genredfs = []
for genre, listofdocids in volumesingenre.items():
    thisgenredf = train1.loc[listofdocids, :]
    thisgenredf.loc[ : , 'volgenre'] = pd.Series([genre] * len(listofdocids), index = listofdocids)
    genredfs.append(thisgenredf)
confident = pd.concat(genredfs)
confident.to_csv('confidentvolumes.csv')

# errordf = train1.loc[errorids, : ]
# errordf.loc[ : , 'readergenre'] = pd.Series(errorconditions)
# errordf.loc[ : , 'pctofpages'] = pd.Series(erroramounts)
# errordf.to_csv('possibleerrors.csv')

leftoverids = alldocids
# renaming to make clearer
leftout = train1.loc[leftoverids, : ]

newcolumns = dict()
for g in genrestocheck:
    newcolumns[g] = pd.Series([0] * len(leftoverids), index = leftoverids)

for g in genrestocheck:
    for d in leftoverids:
        gpct = percentagesbydoc[d][g] / percentagesbydoc[d]['all']
        newcolumns[g].loc[d] = gpct

    leftout.loc[ : , g] = newcolumns[g]

leftout.to_csv('genredividedvols.csv')








