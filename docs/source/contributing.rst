Contributing to PETRARCH
========================

This page is still a bit of a work in progress.

Tutorial
--------

Walk through how to contribute some code/a function to PETRARCH. Explain how
the hooks work.

Tests
-----

Petrarch has a testing suite using pytest and TravisCI. This is run upon a
pull request to GitHub, and notfies us if your version passes. If you want
to test them yourself, just go into the main directory of Petrarch and run

    $ py.test

and the tests will be run. If it fails any tests, the PR will probably not
be accepted unless you provide a compelling reason.



Contributing Process
--------------------

You can check out the latest version of the Phoenix Pipeline by cloning this
repository using `git <http://git-scm.com/>`_.

::

    git clone https://github.com/openeventdata/petrarch.git

To contribute to the phoenix pipeline you should fork the repository, 
create a branch, add to or edit code, push your new branch to your 
fork of the phoenix pipeline on GitHub, and then issue a pull request. 
See the example below:

::

    git clone https://github.com/YOUR_USERNAME/petrarch.git
    git checkout -b my_feature
    git add... # stage the files you modified or added
    git commit... # commit the modified or added files
    git push origin my_feature

Commit messages should first be a line, no longer than 80 characters,
that summarizes what the commit does. Then there should be a space,
followed by a longer description of the changes contained in the commit.
Since these comments are tied specifically to the code they refer to
(and cannot be out of date) please be detailed.

Note that ``origin`` (if you are cloning the forked the phoenix pipeline 
repository to your local machine) refers to that fork on GitHub, *not* 
the original (upstream) repository ``https://github.com/openeventdata/petrarch.git``.
If the upstream repository has changed since you forked and cloned it you can
set an upstream remote:

::

    git remote add upstream https://github.com/eventdata/phoenix_piepline.git

You can then pull changes from the upstream repository and rebasing
against the desired branch (in this example, development). You should 
always issue pull requests against the development branch.

::

    git fetch upstream
    git rebase upstream/development

More detailed information on the use of git can be found in the `git
documentation <http://git-scm.com/documentation>`_.

Coding Guidelines
-----------------

The following are some guidelines on how new code should be written. Of
course, there are special cases and there will be exceptions to these
rules. However, following these rules when submitting new code makes the
review easier so new code can be integrated in less time.

Uniformly formatted code makes it easier to share code ownership. The
petrarch project tries to closely follow the official Python guidelines
detailed in `PEP8 <http://www.python.org/dev/peps/pep-0008/>`__ that
detail how code should be formatted and indented. Please read it and
follow it.

In addition, we add the following guidelines:

-  Use underscores to separate words in non-class names: n\_samples
   rather than nsamples.
-  Avoid multiple statements on one line. Prefer a line return after a
   control flow statement (if/for).
-  Use relative imports for references inside petrarch.
-  Please don’t use ``import *``. It is considered harmful by the
   official Python recommendations. It makes the code harder to read as
   the origin of symbols is no longer explicitly referenced, but most
   important, it prevents using a static analysis tool like pyflakes to
   automatically find bugs in petrarch. Use the numpy docstring standard
   in all your docstrings.

These docs draw heavily on the contributing guidelines for
`scikit-learn <http://scikit-learn.org/>`_.
