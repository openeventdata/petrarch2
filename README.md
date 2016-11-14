PETRARCH-2
==========

[![Join the chat at https://gitter.im/openeventdata/petrarch2](https://badges.gitter.im/openeventdata/petrarch2.svg)](https://gitter.im/openeventdata/petrarch2?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Documentation Status](https://readthedocs.org/projects/petrarch2/badge/?version=latest)](http://petrarch2.readthedocs.org/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/openeventdata/petrarch2.svg?branch=master)](https://travis-ci.org/openeventdata/petrarch2)
[![Code Health](https://landscape.io/github/openeventdata/petrarch2/master/landscape.svg?style=flat)](https://landscape.io/github/openeventdata/petrarch2/master)

[![Caerus logo](http://caerusassociates.com/wp-content/uploads/2012/03/Caerus_logo.png)](http://caerusassociates.com/wp-content/uploads/2012/03/Caerus_logo.png)

Code for the new Python Engine for Text Resolution And Related Coding Hierarchy (PETRARCH-2) 
event data coder. The coder now has all of the functions from the older TABARI coder 
and the new CAMEO.2.0.txt verb dictionary incorporates more syntactic information and is far
simpler than the previous version.


For more information, please read the Petrarch2.pdf file in this directory and visit the (work-in-progress)
[documentation](http://petrarch2.readthedocs.org/en/latest/#).

##First, a couple of notes...

It is possible to run PETRARCH-2 as a stand-alone program. Most of our
development work has gone into incorporating PETRARCH-2 into a full pipeline of
utilities, though, e.g., the [Phoenix pipeline](https://github.com/openeventdata/phoenix_pipeline).
There's also a RESTful wrapper around PETRARCH and CoreNLP named
[hypnos](https://github.com/caerusassociates/hypnos). It's probably worthwhile
to explore those options before trying to use PETRARCH as a stand-alone. 

That said, there are a variety of situations -- most notably those where you have already downloaded a set of 
stories -- where you will, in fact, want to run PETRARCH in a batch mode rather than as part of a pipeline.
If you are in this situation, see the section "Processing stories outside the pipeline."

##Does this work?

As with all open source projects, you are probably wondering whether this code really works "in the wild" 
or merely just on enough cases to satisfy our overlords before we went on to something else. On this, we
have good news: it's quite robust. We're aware of at least the following large-scale applications:

* The near-real-time [Phoenix](http://phoenixdata.org/data) dataset has been running  has been running more
or less continuously (with the crashes largely due to our cloud services provider) for over two years working with 
hypnos and PETRARCH-1

* An on-going academic project is using hypnos and PETRARCH-2 to code more than 30,000 event per day in 
near real time

* An experimental project coded about 25-million sentences in batch mode with both PETRARCH 1 and 2

* A project based in Amazon Web Services has integrated PETRARCH-2, CoreNLP and Mordecai into a system coding
more than 1,000 stories per hour

* At least two academic projects are using the system to code long-time-frame datasets which will go back to 
around 1980; this data should be public in early 2017

While it is the case that the world will continue to throw ever-more-novel 
examples of wild and crazy source texts (which, of course, we'd love to see entered as issues, or even better,
submitted as bug fixes), and it is quite possible one or more of these will come your way and
crash either CoreNLP or PETRARCH, generally this is software that, indeed, works in the wild, not
just in the lab. None of the major deployments above are simple "plug-and-play" -- all involve a certain
amount of customization, particularly in the initial formating of source texts and getting all of the 
various components working smoothly in various hardware environments -- but fundamentally, yes, it works.

##Installing
If you do decide you want to work with PETRARCH-2 as a standalone program, it is possible to install:


``pip install git+https://github.com/openeventdata/petrarch2.git``


This will install the program with a command-line hook. You can now run the program using:

``petrarch <COMMAND NAME> [OPTIONS]``

You can get more information using:

``petrarch -h``

**StanfordNLP:**

There was a time where Stanford CoreNLP was incorporated directly into PETRARCH-1, but due
to operating system differences that we don't want to deal with, this is no longer the case.
We recommend [this dockerized API](http://github.com/chilland/ccnlp) if you need to incorporate
a CoreNLP parse into a script, or the Stanford website has a nice [web app](http://nlp.stanford.edu:8080/corenlp/),
 where if you select the "Pretty Print," output option, it'll give you the 
syntactic parse in Treebank form. Or if you're not looking to edit Petrarch itself and just
use its functionality, [hypnos](https://github.com/caerusassociates/hypnos) is an easier option.


##Running PETRARCH-2

Currently, you can run PETRARCH-2 using the following command if installed:

``petrarch2 batch [-i <INPUT FILE> ] [-o [<OUTPUT FILE>]``

If not installed:

``python petrarch2.py batch -i <INPUT FILE> -o <OUTPUT FILE>``

You can see a sample of the input/output by running (assuming you're in the
PETRARCH2 directory):

``petrarch2 batch -i ./petrarch2/data/text/GigaWord.sample.PETR.xml -o test.txt``

This will return a file named `evts.test.txt`.

There's also the option to specify a configuration file using the ``-c <CONFIG
FILE>`` flag, but the program will default to using ``PETR_config.ini``.

When you run the program, a ``PETRARCH.log`` file will be opened in the current
working directory. This file will contain general information, e.g., which
files are being opened, and error messages.

But seriously, if you are doing near-real-time coding and need geolocation, you should probably use [hypnos](https://github.com/caerusassociates/hypnos) rather than run PETRARCH as a standalone program.

##Unit tests

Commits should always successfully complete the PyTest command

``py.test``

Naturally you need PyTest installed for this to work. Commits will be tested
by TravisCI upon Pull Request to the master directory, and will tell us whether
the version has passed the tests. If for whatever reason you need to change the 
tests or add cases to the test file, state that in the PR description. 

##PETRARCH-1 vs. PETRARCH-2

While these two programs share a name, actor dictionary formats and input formats, they are effectively
two different programs:

* Because it used the verb dictionaries from [TABARI](http://eventdata.parusanalytics.com/software.dir/tabari.html), a coder based on shallow parsing, PETRARCH-1 made relatively little use of the CoreNLP constituency parse beyond parts-of-speech
markup and noun-phrase markup. PETRARCH-2 makes full use of the deep parse.

* The verb dictionary for PETRARCH-2 is both different in the way it specifies patterns, and significantly simpler than the dictionaries in PETRARCH-1.

* PETRARCH-2 actually incorporates some elements of the CAMEO ontology -- notably determining the scope of CAMEO 04 "CONSULT" events -- into the coder itself, as well as effectively redefining the 04 category compared to the
TABARI and PETRARCH-1 implementations. In the PETRARCH-1 system, ontology implementation is done solely in the dictionaries.

* Because PETRARCH-2 is more reliant on the deep parse, it is more sensitive to parsing errors on poorly-formed sentences. However, the deep parsing makes it much more robust against incorrectly assigning target actors.

* PETRARCH-1 has a far more extensive validation suite than PETRARCH-2 has unit tests, and unfortunately due to the differences in the specification of verb patterns, the two are not compatible. (We would enthusiastically welcome additions to the unit tests!)

Despite these differences, the aggregate distributions of events in CAMEO 2-digit categories produced by the two systems in a test against a large corpus consisting of a wide variety of source materials (that is, not just sources with well-edited English) are quite similar, even though the results on individual stories only coincide about 40% of the time.

##Processing stories outside the pipeline

hypnos and the Phoenix pipeline more generally are designed for [near-real-time processing] (https://en.wikipedia.org/wiki/Real-time_computing#Near_real-time) and consequently involve both
web scraping and dynamic storage of those results into a MongoDB database. While this is 
appropriate when your source texts are coming immediately from the web, many applications of
event data use texts which have already been downloaded -- typically from an aggregator such
as Lexis-Nexis, Factiva, or ProQuest -- and simply need to be coded from a set of files. In 
that case, the scrapping and MongoDB storage can be skipped, and instead the processing would
involve the following steps

1. Pull out the story texts from your inputs and create one text file per story.

2. Pass a list of those files in CoreNLP: your command will end up looking something like

```
java -cp "*" -Xmx2g edu.stanford.nlp.pipeline.StanfordCoreNLP -sentences newline -annotators tokenize,cleanxml,ssplit,pos,lemma,ner,parse,dcoref -parse.model edu/stanford/nlp/models/srparser/englishSR.ser.gz  -filelist cline.files.txt -outputDirectory cline_exper1_output
```

   where "cline.files.txt" was just a simple list of the files, one per line.
   
   [and the .md formatter for some reason feels compelled to restart list numbering now...]

3.  CoreNLP then grinds through all of these, and puts the output in the directory "cline_exper1_output" (per the final command line option), using the original file name plus a ".out" suffix. This is an XML file, and the parses are in the field <parse> -- there is one for each sentence in the story.

4. Take all of those files (or, more prudently, a series of subsets to keep the file sizes down) and convert these to the PETRARCH XML format, which looks like the follow (line feeds in the parse aren't significant but were added for readability)

```
    <Sentences>
 
    <Sentence date = "20150805" id ="NULL-1107c5f6-7a30-4aa8-8845-7db535b7504d_1" source = "en1_6-10_story+10+ISO:CHN" sentence = "True">
    <Text>
    Javanese Grand Waffalo Shinzo Abesson has asked the colonial vizarate to look into the alleged spying activities on the
    Javanese tribes and companies raised by the Wikileaks website in telephone talks with colonial vizar Joel Bowden
    Wednesday, local media reported .
    </Text>
    <Parse>
    (ROOT (S (NP (JJ Javanese) (NNP Grand) (NNP Waffalo) (NNP Shinzo) (NNP Abesson)) 
    (VP (VBZ has) 
    (VP (VBN asked) 
    (NP (NP (DT the) (NNP colonial) (NN vizarate)) (S 
    (VP (TO to) 
    (VP (VB look) 
    (PP (IN into) 
    (NP (NP (NP (DT the) (JJ alleged) (VBG spying) (NNS activities)) 
    (PP (IN on) 
    (NP (NP (DT the) (JJ Javanese) (NN tribes) (CC and) (NNS companies)) 
    (VP (VBN raised) 
    (PP (IN by) (NP (DT the) (NNP Wikileaks) (NN website))) 
    (PP (IN in) 
    (NP (NP (NN telephone) (NNS talks)) 
    (PP (IN with) (NP (NNP colonial) (NNP vizar) (NNP Joel) (NNP Bowden) (NNP Wednesday))))))))) 
    (, ,) 
    (NP (JJ local) (NNS media)))))))) 
    (VP (VBD reported)))) 
    (. .))) 
    </Parse>
 
    </Sentence>
    <Sentence date = "20150903" id ="NULL-1105dabf-7eb5-452b-9d02-9b4d6ecfa718_1" source = "en1_6-10_story+10+ISO:LVA" sentence = "True">
    <Text>
    On September 2, 2015, Lorien dopplemats confirmed the European Disunion has extended the sanctions imposed on Mordor
    and Harad citizens supporting pro-Elf separatists in Eastern Mordor, for a further six months .
    </Text>
    <Parse>
    (ROOT (S 
    (PP (IN On) (NP (NNP September) (CD 2) 
    (, ,) 
    (NP (CD 2015)) 
    (, ,) 
    (NP (JJ Lorien) (NNS dopplemats)))) 
    (VP (VBD confirmed) 
    (SBAR (S (NP (DT the) (NNP European) (NNP Disunion)) 
    (VP (VBZ has) 
    (VP (VBN extended) (S (NP (DT the) (NNS sanctions)) 
    (VP (VBN imposed) 
    (PP (IN on) 
    (NP (NP (ADJP (JJ Mordor) (CC and) (JJ Harad)) (NNS citizens)) 
    (VP (VBG supporting) 
    (NP (NP (JJ pro-Elf) (NNS separatists)) 
    (PP (IN in) (NP (NNP Eastern) (NNP Mordor))))))))) 
    (, ,) 
    (PP (IN for) (NP (DT a) (JJ further) (CD six) (NNS months)))))))) 
    (. .))) 
    </Parse>
    </Sentence>
 
    </Sentences>
```
 
That is, all your "glue" program needs to do here is put the original text in the <Text> field and the parsed text in the <Parse> field, plus add a date and a unique identifier plus whatever else you want to pull in. 

4.  Run that through PETRARCH-2: if you have a large number of files (which is typical when you're in a batch 
situation) you'll want to break these PETRARCH-2 inputs into multiple files, then run them using in a script or across multiple machines, finally combine the output files with the coded events (multiple-event filtering can also be done at this stage if you are so inclined).

5. The Mordecai geolocation program is a separate process: run it on the original texts and then merge that with the events if you need geolocation.


That's it: the downside of the file-based approach is you are left with a gadzillion little files in steps [1] and [3] and the disk-based rather than RAM-based approach is doubtlessly a bit slower, but CoreNLP is the main bottleneck. Upside is these are really basic discrete steps and easy to diagnose.

In terms of time required using this approach, a ca. 2013 iMac (3.2 Ghz Intel Core i5 with 16Gb RAM) processed about 2500 stories per hour in CoreNLP (using the shift-reduce parser), running two instances of the program, then roughly 900,000 sentences per hour with a single instance PETRARCH-2. These figures were from a largely unfiltered Lexis-Nexis corpus, and a small number of stories (typically those where sentence segmenting went awry) used a disproportionate amount of time because CoreNLP pursued a large number of dead-ends before giving up: pre-filtering to insure that sentences are typical of those which will generate events should increase the overall coding speed somewhat. We've yet to do speed checks on Amazon Web Services instances though they are probably roughly comparable (both CoreNLP and PETRARCH-2 work fine on AWS).



