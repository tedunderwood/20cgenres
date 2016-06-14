# maketags.py
import os, csv, json

fields = ['page', 'tag']

def creatematches(sourcedir, targetdir):

    sourcevols = [x for x in os.listdir(sourcedir) if x.endswith('json')]
    for vol in sourcevols:
        volumepath = os.path.join(sourcedir, vol)
        with open(volumepath, encoding = 'utf-8') as f:
            thestring = f.read()

        thejson = json.loads(thestring)
        pagedata = thejson['features']['pages']
        numpages = len(pagedata)

        targetfile = vol.replace('.json', '.csv')
        targetpath = os.path.join(targetdir, targetfile)
        with open(targetpath, mode = 'w', encoding = 'utf-8') as f:
            writer = csv.DictWriter(f, fieldnames = fields)
            writer.writeheader()
            for i in range(numpages):
                row = dict()
                row['page'] = i
                row['tag'] = ''
                writer.writerow(row)

sourcedir = 'counts'
targetdir = 'tags'
if not os.path.isdir(targetdir):
    os.mkdir(targetdir)

creatematches(sourcedir, targetdir)
