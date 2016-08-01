#!/usr/bin/env python3

# Based on inferfromreaders.

# We read volume metadata and produce page metadata,
# confirming along the way that the number of pages
# in our metadata matches the number in the json

import csv, os, sys, shutil
from collections import Counter
import numpy as np
import pandas as pd

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils
import parsefeaturejsons as parser

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

train1 = pd.read_csv('../bzipmeta.csv', dtype = 'object', index_col = 'docid')

tidx = set(train1.index.values)
for filename in allfiles:
    docid = filename.replace('.csv', '')
    if utils.dirty_pairtree(docid) not in tidx:
        print(docid)

genrestocheck = ['fic', 'poe']
equivalences = {'non', 'bio', 'other'}

volumesingenre = dict()
for g in genrestocheck:
    volumesingenre[g] = []

alldocids = set()

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
        if g in genrectr and genrectr[g] > (genrectr['all'] / 2):
            volumesingenre[g].append(filename)

jsondirs = ['/Volumes/TARDIS/work/hathifiles/counts/', '/Volumes/TARDIS/work/hathifiles/secondcounts/']

numlost = 0

numpages = dict()
destination = '/Users/tunder/work/pagedata'

for g in genrestocheck:

    for filename in volumesingenre[g]:
        docid = utils.dirty_pairtree(filename.replace('.csv', ''))
        jsonname = filename.replace('.csv', '.basic.json.bz2')
        found = False
        for directory in jsondirs:
            thispath = os.path.join(directory, jsonname)
            if os.path.isfile(thispath):
                vol = parser.PagelistFromJson(thispath, docid)
                print(vol.numpages)
                destinationpath = os.path.join(destination, jsonname)
                shutil.copyfile(thispath, destinationpath)
                found = True
                numpages[docid] = vol.numpages

        if not found:
            numlost += 1

outcols = list(train1.columns.values)
outcols.append('groupid')
outcols.append('pageid')
outcols.append('class')

toignore = {'/Volumes/TARDIS/work/readers/april20trondson/tags/inu.39000004302985.csv', '/Volumes/TARDIS/work/readers/march27trondson/tags/mdp.39015030775509.csv'}

for g in genrestocheck:
    print(g)
    thisdf = []
    for filename in volumesingenre[g]:
        if 'metadat' in filename:
            print(filename)
            continue
        docid = utils.dirty_pairtree(filename.replace('.csv', ''))
        binarized = []
        for path in paths[filename]:
            if path in toignore:
                continue
            recordedgenres = []

            with open(path, encoding = 'utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    recordedgenres.append(row['tag'])

            if len(recordedgenres) != numpages[docid]:
                print('Error in page count in doc ' + docid)
                print(paths[filename])

            binarygenres = [1] * len(recordedgenres)

            # the following loop zeroes out the front
            # until it hits two successive pages of
            # the expected genre
            for idx, g1 in enumerate(recordedgenres):
                if g1 != g:
                    binarygenres[idx] = 0
                elif idx + 1 >= len(recordedgenres):
                    break
                elif g1 == g and recordedgenres[idx + 1] != g:
                    binarygenres[idx] = 1
                elif g1 == g and recordedgenres[idx + 1] == g:
                    break

            for idx, g1 in reversed(list(enumerate(recordedgenres))):
                if g1 != g:
                    binarygenres[idx] = 0
                elif idx - 1 < 0:
                    break
                elif g1 == g and recordedgenres[idx - 1] != g:
                    binarygenres[idx] = 1
                elif g1 == g and recordedgenres[idx - 1] == g:
                    break

            binarized.append(binarygenres)
        pagediscrepancy = 0
        if len(binarized) > 1:
            for idx, bingenre in enumerate(binarized[0]):
                if bingenre != binarized[1][idx]:
                    pagediscrepancy += 1

            print('DISCREP: ' + str(pagediscrepancy))
            print(docid)

        for idx, bgenre in enumerate(binarygenres):
            # we are arbitrarily using the last one
            # but there were in practice no discrepancies, so ...

            corerow = train1.loc[docid, : ]
            newrow = corerow.append(pd.Series(docid, index = ['groupid']))
            pageid = docid + '||' + str(idx)
            newrow = newrow.append(pd.Series(pageid, index = ['pageid']))
            newrow = newrow.append(pd.Series(bgenre, index = ['class']))
            thisdf.append(newrow)

    outpath = g + '.csv'
    thisdf = pd.DataFrame(thisdf)
    thisdf.to_csv(outpath)





























