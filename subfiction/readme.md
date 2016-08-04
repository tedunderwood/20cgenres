subfiction
==========

Once the initial fiction dataset was created (ficpost1922.csv), I produced two models -- one of nonfiction mistakenly included, and another of works for a "juvenile audience."

implementsubfic.py applies these models:

annotatedfiction.csv is produced; the new models create columns for nonfictionprob and juvenileprob. There are also a number of older columns inherited from earlier processes. The "rawprobability" that originally got the volume included, the proportion of words in a generic list of 1000 most common english words, wordcount, etc. Also "metadatalikely" and "metadatasuspicious," which mean roughly:

a) Is the volume explicitly tagged "Fiction," "a novel," etc? and ...
b) Is it explicitly tagged biography / autobiography / description and travel / directory / dictionary? (Categories of things often conflated with fiction. Directories get included because _lots of names_.)

filterframes.py applies some adhoc rules to these various columns in order to exclude some stuff and produce filteredfiction.csv. **Note:** if you're looking for a place to be suspicious of my procedures, this ad hoc step is a good place. I tried to be cautious, but some people will want a tighter or looser cutoff; will provide the original metadata and probabilities so people can make their own calls.