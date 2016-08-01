page
====

Scripts to do page-level modeling, which trims front and back matter, including nonfiction prefaces. Note that in the updated (2016) workflow this only runs _after_ volume-level modeling.

At an early stage of writing these I had a fantasy that these scripts could be integrated with the volume-level scripts, creating a single general solution. But it's not worthwhile; there are too many differences. Metadata has to be handled differently, because pages are grouped at the volume level and those groups need to be preserved when pages are assigned to training/test sets. Positive and negative classes are more simply binary; it's no longer necessary to permit fic-against-bio or fic-against-everything, etc. Also, there's a smoothing operation that has to be performed after page-level prediction.

In short, a lot of differences, and it made more sense to fork the code than to refactor and generalize.

makepagemeta.py
---------------
Makes a page-level model.

parallelizepagemodel.py
-----------------------
Parallelizes the previous script so we can grid search on parameters.