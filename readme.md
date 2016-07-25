train20
=======

Code and data used to train models of 20c literary genres. The governing strategy here is to slice strategically, creating progressively smaller sets and progressively better models.

To achieve this, we start with volume-level discriminations, and then work downward to the page level, training page-level models _only within_ literary genres.

But also, even within the volume-level process, we work through successive eliminations — first constituting a rough list of possible fiction candidates by modeling fiction-against-everything, and then paring away things that a more precise model suggests are actually biography, drama, or poetry.

Needless to say, no raw texts from in-copyright volumes will be exposed in this process. The modeling process works with extracted features, and even those are not exposed here.

bzipmeta.csv
------------
Created June 2016. Contains metadata for all the files with extracted features in TARDIS/work/hathifiles. These should also have volume-level summaries in TARDIS/work/train20.


inferfromreaders.py
-------------------
First stage of constructing a training set. This looks at 362 volumes tagged by undergrads at a page level and sorts them into volume-level groups. Produces *confidentvolumes.csv* as well as **genredividedvols.csv.** The latter are not used in volume-level classification.

manualtagging.py
----------------
Amplifies the page-level training set with several hundred volume-level genre tags assigned by Underwood. Places these in **taggedvolumes.csv.**

createtrainingset.py
--------------------
Fuses the output of the previous two stages in order to produce **maintrainingset.csv.** This becomes the metadata used in ...

trainamodel.py
--------------
Functions centrally needed for creating models of one genre against another genre, or of one genre against all other genres. Is called by ...

parallelmodel.py
----------------
Which uses multiprocessing to accelerate grid search, among other things.


implementmodel.py
-----------------
is the business end of this whole workflow, taking an ensemble of models produced by trainamodel.py and coordinating them (with some ad-hoc rules) in order to actually classify texts.