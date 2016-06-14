#!/usr/bin/env python3

# Based on gathertags, this goes further by identifying owners and
# sorting files by genre.

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

multipleowners = []
for filename, owners in readerowners.items():
    if len(owners) > 1:
        multipleowners.append(filename)

print(len(multipleowners))

sumpages = 0
sumdiffs = 0
disagreements = Counter()

for filename in multipleowners:
    print()
    print(filename)
    print(len(paths[filename]))
    existing = dict()
    allcounts = 0
    differences = 0
    for p in paths[filename]:
        with open(p, encoding = 'utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'tag' not in row:
                    print(p)
                    break
                allcounts += 1
                page = row['page']
                tag = row['tag']
                if page not in existing:
                    existing[page] = tag
                else:
                    if tag != existing[page]:
                        differences += 1
                        thistuple = (tag, existing[page])
                        if thistuple not in disagreements:
                            thistuple = (existing[page], tag)
                        disagreements[thistuple] += 1
    print(differences/allcounts)
    sumpages += allcounts
    sumdiffs += differences
    if (differences / allcounts) > 0.1:
        print(paths[filename])

print()
print(sumdiffs / sumpages)

for key, value in disagreements.items():
    print(key, value)

allfiles = tagset

train1 = pd.read_csv('bzipmeta.csv', dtype = 'object', index_col = 'docid')

tidx = set(train1.index.values)
for filename in allfiles:
    docid = filename.replace('.csv', '')
    if utils.dirty_pairtree(docid) not in tidx:
        print(docid)

ficlist = []
nonficlist = []
errorlist = []

for filename, owners in readerowners.items():
    path = paths[filename][0]
    if 'metadat' in filename:
        print(filename)
        continue
    docid = utils.dirty_pairtree(filename.replace('.csv', ''))
    genre = train1.loc[docid, 'sampledas']
    with open(path, encoding = 'utf-8') as f:
        reader = csv.DictReader(f)
        ficct = 0
        allct = 0
        for row in reader:
            allct += 1
            if row['tag'].lower() == 'fic':
                ficct += 1
        ficpct = ficct / allct
        if genre == 'fic' and ficpct < 0.7:
            print('ERROR', genre, docid)
            errorlist.append((docid, ficpct))
            if ficpct < 0.4:
                nonficlist.append(docid)
        elif genre == 'fic':
            ficlist.append(docid)
        elif genre != 'fic' and ficpct > 0.3:
            print('ERROR', genre, docid)
            errorlist.append((docid, ficpct))
            if ficpct > 0.8:
                ficlist.append(docid)
        else:
            nonficlist.append(docid)

fiction = train1.loc[ficlist, :]
nonfiction = train1.loc[nonficlist, :]

fiction.loc[ :, 'class'] = pd.Series([1] * len(ficlist), index = fiction.index)
nonfiction.loc[ :, 'class'] = pd.Series([0] * len(nonficlist), index = nonfiction.index)

forclassification = pd.concat([fiction, nonfiction])
forclassification.to_csv('firsttrainingset.csv')

errorids = [x[0] for x in errorlist]
errors = [x[1] for x in errorlist]
errors = pd.Series(errors, index = errorids)

errordf = train1.loc[errorids, :]
errordf.loc[ : , 'ficpct'] = errors
errordf.to_csv('errorlist.csv')





