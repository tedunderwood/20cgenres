# pagebrowser.py

import json, csv, os
from collections import Counter

validtags = ['front', 'back', 'non', 'bio', 'fic', 'poe', 'dra', 'ads']

def givehelp():
    print("This is a browser that allows you to load volumes and browse")
    print("wordcount information at a page level. It assumes that the")
    print("word counts are in a subdirectory called /counts located")
    print("immediately below this application. Legal commands include:")
    print("")
    print("'quit': quits this browser")
    print("'load' X: loads a volume counts/X")
    print("integer: prints wordcounts for page #integer of the loaded vol")
    print("anyword: finds pages in the loaded vol that contain anyword")
    print("anyword otherword: finds pages in the loaded vol that contain anyword and otherword")
    print("'checkvols': checks the counts in /counts against the tags in /tags, and reports")
    print("           : whether volumes have been tagged appropriately")
    print("'help' : prints this list of commands")
    print("")
    print("Note that you can't search for 'quit,' 'load,' or 'help' as words")
    print("in a volume. They'll be interpreted as commands.")

def makealphalist(adict):
    alphalist = []
    for key, value in adict.items():
        alphalist.append(key)
    alphalist.sort()

    return alphalist

def printlist(alist):
    line = ""
    ctr = 0
    for word in alist:
        line = line + word + " "
        ctr += 1
        if ctr > 5:
            print(line)
            line = ""
            ctr = 0
    if len(line) > 0:
        print(line)

class LoadedVolume:

    # Mainly a data object that contains page-level wordcounts
    # for a volume.

    def __init__(self, volumepath):
        '''initializes a LoadedVolume by reading wordcounts from
        a json file'''

        with open(volumepath, encoding = 'utf-8') as f:
            thestring = f.read()

        thejson = json.loads(thestring)
        pagedata = thejson['features']['pages']
        self.numpages = len(pagedata)
        self.pagesets = []
        self.bodylists = []
        self.headerlists = []
        self.totalcounts = []

        for i in range(self.numpages):
            wordcounts = Counter()
            headercounts = Counter()
            totalwords = 0
            thispage = pagedata[i]

            bodywords = thispage['body']['tokenPosCount']
            for token, partsofspeech in bodywords.items():
                lowertoken = token.lower()
                for part, count in partsofspeech.items():
                    totalwords += count
                    wordcounts[lowertoken] += count

            headerwords = thispage['header']['tokenPosCount']
            for token, partsofspeech in headerwords.items():
                lowertoken = token.lower()
                for part, count in partsofspeech.items():
                    totalwords += count
                    headercounts[lowertoken] += count

            # You will notice that I treat footers as part of the body
            # In practice, footers are rarely interesting.

            footerwords = thispage['footer']['tokenPosCount']
            for token, partsofspeech in footerwords.items():
                lowertoken = token.lower()
                for part, count in partsofspeech.items():
                    totalwords += count
                    wordcounts[lowertoken] += count

            thisset = set(headercounts).union(set(wordcounts))
            self.pagesets.append(thisset)

            thisbody = makealphalist(wordcounts)
            self.bodylists.append(thisbody)

            thisheader = makealphalist(headercounts)
            self.headerlists.append(thisheader)

            self.totalcounts.append(totalwords)

        # We are done with the __init__ method for this volume.

    def printpage(self, pageint):
        if pageint > self.numpages:
            print("You're requesting page # " + str(pageint))
            print("but this volume only has " + str(self.numpages) + " pages.")
        else:
            print("Page " + str(pageint) + " has " + str(self.totalcounts[pageint]) + " words.")
            print("HEADER:")
            h = self.headerlists[pageint]
            printlist(h)
            print("BODY:")
            b = self.bodylists[pageint]
            printlist(b)

    def findmatches(self, wordlist):
        '''
        We want to print all the pages that have all the words in
        wordlist. To do that we start by creating a list of all pages.
        Then we iterate through wordlist, and remove any page that
        lacks any word.
        '''

        allpages = set([x for x in range(self.numpages)])
        for word in wordlist:
            for idx, aset in enumerate(self.pagesets):
                if idx in allpages and word not in aset:
                    allpages.remove(idx)

        if len(allpages) == 0:
            print("We found no pages matching: ")
            print(wordlist)
        else:
            printlist([str(x) for x in allpages])

def checktags(tagpath, npages):
    '''
    Confirms that all pages are either tagged or
    untagged. If tagged, confirms that they belong
    to valid tagset.

    It assumes that the tagfile will take the form of
    a csv, in utf-8 format, with two columns, "page" and
    "tag."
    '''
    global validtags

    # Here are some things that could go wrong:

    found = True
    inorder = True
    allvalid = True
    invalids = []

    ctr = 0
    blanks = 0

    try:
        with open(tagpath, encoding = 'utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                page = int(row['page'])
                tag = row['tag'].strip()
                # note that we strip blanks

                if ctr != page:
                    inorder = False

                if not tag or tag == '':
                    blanks += 1
                elif tag not in validtags:
                    invalids.append((page, tag))
                    allvalid = False
                ctr += 1
    except:
        found = False

    done = False

    if not found:
        print("File " + tagpath + " was not found, or not correctly formatted.")
    elif not inorder:
        print("The page numbers in " + tagpath + " are out of order.")
    elif ctr != npages:
        print("The tagfile " + tagpath + " has " + str(ctr) + " pages; I expected " + str(npages))

    if blanks == ctr:
        print(tagpath + " not yet tagged.")
    elif blanks == 0 and allvalid:
        print(tagpath + " completely tagged; ready to review.")
        done = True
    elif blanks > 0 and allvalid:
        print(tagpath + " has some valid tags, but still lacks tags for " + str(blanks) + " pages.")
    elif not allvalid:
        print("The tagfile " + tagpath + " contains the following invalid tags: ")
        for page, tag in invalids:
            print(str(page) + " : " + tag)
        if blanks > 0:
            print("This file also contains " + str(blanks) + " blank rows.")
    print()

    return found, done

def checkvolumes():
    '''
    This function aligns the volumes in two subdirectories.
    '''

    countvols = [x for x in os.listdir('counts') if x.endswith('json')]
    tagvols = [x for x in os.listdir('tags') if x.endswith('csv')]

    ncounts = len(countvols)
    ntags = len(tagvols)

    print("There are " + str(ncounts) + " count files under /counts")
    print("and " + str(ntags) + " tag files under /tags.")

    volpairs = []
    matches = 0
    for vol in countvols:
        match = vol.replace('json', 'csv')
        if vol.endswith('json') and match in tagvols:
            matches += 1
            volpairs.append((vol, match))

    print(str(matches) + " of those volumes match.")

    numfound = 0
    numdone = 0
    print()

    for countfile, tagfile in volpairs:
        countpath = os.path.join('counts', countfile)
        cvol = LoadedVolume(countpath)
        npages = cvol.numpages

        tagpath = os.path.join('tags', tagfile)
        found, done = checktags(tagpath, npages)

        if found:
            numfound += 1
        if done:
            numdone += 1

    print('I found correctly formatted tag files in ' + str(numfound) + " cases.")
    print('Of those, ' + str(numdone) + ' were completely tagged and ready to submit.')


# MAIN LOOP BEGINS HERE.

keepgoing = True
hasvolume = False

givehelp()
while keepgoing:

    print()
    user = input(': ')
    commands = user.split()
    numwords = len(commands)
    print()

    if numwords < 1:
        continue
    elif commands[0] == 'quit':
        keepgoing = False
        continue
    elif commands[0] == 'load':
        if numwords < 2:
            print("Load what?")
            continue
        else:
            datapath = os.path.join('counts', commands[1])
            if os.path.isfile(datapath):
                volume = LoadedVolume(datapath)
                hasvolume = True
                print("You have loaded a volume with " + str(volume.numpages) + " pages.")

            else:
                print('I cannot find ' + datapath)
                continue
    elif commands[0] == 'help':
        givehelp()

    elif commands[0] == 'checkvols':
        checkvolumes()

    elif numwords > 1:
        volume.findmatches(commands)
        # Note that this gives you a way to search for integer page numbers
        # as strings within a volume by doing e.g. "the 212."

    elif commands[0].isdigit():
        if not hasvolume:
            print('I cannot give you a page until you load a volume.')
            continue
        else:
            volume.printpage(int(commands[0]))

    else:
        volume.findmatches(commands)










