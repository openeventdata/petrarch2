Input Formats
=============

There are three (fairly) unique input formats for PETRARCH: the processing
pipeline, the XML input, and the validation routine input. The following
sections describe the details of these input types and formats.

Pipeline
--------

The pipeline input is made for integration with the `processing pipeline <http://phoenix-pipeline.readthedocs.org/en/latest/>`_.
The processing pipeline has tight integration with a MongoDB instance. Thus,
the relevant PETRARCH functions are designed to work with this input format.
Specifically, the input is a list of dictionaries, with each dictionary holding
an single entry in the MongoDB instance. The PETRARCH function to interface
with the pipeline is ``run_pipeline()``. This function is designed to be
dropped into the main processing pipeline script with a call such as:

``output = petrarch.run_pipeline(holding, write_output=False)``

where ``holding`` is the list of dictionaries described above. For more
information about ``run_pipeline()`` and its output formats, please view the
relevant documentation.

XML Input
---------

The main input format for PETRARCH is an XML document with each entry in the
document a sentence or story to be parsed. The inputs can be either individual
sentences or entire stories. Additionally, the input can contain pre-parsed
information from StanfordNLP or just the plain text with the Stanford parse
left up to TABARI. Whether the input is parsed or not is indicated using the
``-P`` flag in the PETRARCH command-line arguments. 

In general, the XML format is:

::

    <Sentences>

    <Sentence date = "YYYYMMDD" id = "storyString_sent#" source = "AFP" sentence = "Boolean">
    <Text>
    </Text>
    <Parse>
    </Parse>
    </Sentence>

    </Sentences>


Again, the ``<Parse></Parse>`` blocks are optional. Each attribute of the
entries has a fairly obvious role. The ``date`` attribute is the date of the
entry in a ``YYYYMMDD`` format. The ``id`` attribute is a unique ID for the
entry. If the entry is a single sentence, the format of the ID should be
``storyString_sentNumber`` or ``ABCDEFGHIJKLM_1`` which would indicate story
``ABCDEFGHIJKLM`` and sentence 1. The ``sentence`` attribute indicates whether
the text in the entry is from a single sentence or a block of sentences, such
as from the lead paragraph of a news story. Finally, the ``source`` attribute
indicates what source the material came from, such as Agence-France Presse.


Validation Input
----------------

Validation files are used for debugging and unit testing, combining the
contents of a project file and text file as well as providing information on
the correct coding for each record. This approach is used based on some
decidedly aggravating experiences during the TABARI development where the
validation records and the required .verbs and .actors files were not properly
synchronized.

The general format of the file is:

::

    <Validation>

    <Environment>
    </Environment>		

    <Sentences>

    <Sentence>
    <Text>
    </Text>
    <Parse>
    </Parse>
    </Sentence>

    </Sentences>

    </Validation>

These elements are described in greater detail below.

**Required elements in the <Environment> block:**

::

    <Environment>
            <Verbfile name="<filename>"></Verbfile>
            <Actorfile name="<filename>"></Actorfile>
            <Agentfile name="<filename>"></Agentfile>
    </Environment>

There can only be one actorfile, unlike in the config file, which allows a list.

**Options elements in the <Environment> block:**

``<Include categories="<space-delimited list of categories to include in test>">``

If 'valid' is included as a category, only records containing valid="true" in <SENTENCE> will be evaluated.

``<Exclude categories="<space-delimited list of categories to exclude in test>">``

If a category is in both lists, the case is excluded. But please don't do this.

``<Pause value="<always, never>">``

|        Pause conditions:
|                always  -- pause after every record
|                never   -- never pause (errors are still recorded
|                                        in file)
|                stop    -- exit program on the default condition
|                            [below]
|                default -- pause only when EventCodes record
|                            doesn't correspond to the generated
|                            events or if there is no EventCodes
|                            record

**General record fields:**

All of these tags should occur on their own lines.

``<Sentence>...</Sentence>``:

Delimits the record. The <Sentence...> tag can have the following fields: date: date of the text in YYYYMMDD format. This is required; if it is not present the record will be skipped


|            id: identification string in any format [optional] category:
|                category in any format; this is used by the <Include> and
|                <Exclude> options [optional]
|
|            place: code to be used for anonymous actors [optional]

``</Text>...</Text>``:

Delimits the source text. This is used only for the display. The tags should occur on their own lines

``<Parse>...</Parse>``:

Delimits the TreeBank parse tree text: this used only for the actual coding.

**Required elements in each record for validation:**

One or more of these should occur prior to the TreeBank. If none are present,
the record is coded and the program pauses unless <Pause value = "never'> has
been used.

``<EventCodes sourcecode="<code>" targetcode="<code>" eventcode="<code>">``

``<EventCodes noevents = "True">``:

Indicates the record generates no events. Presently, system just looks for the presence of a 'noevents' attribute. This is also equivalent to no <EventCodes record, but better to state this explicitly.

**Optional elements in record:**

``<Skip>``:

Skip this record without coding

``<Stop>``:

Stop coding and exit program

``<Config option ="<config.ini option from list below>" value ="<value>">``:

Change values of PETR_config.ini globals.

Currently works for: new_actor_length, require_dyad, stop_on_error, comma_*

**Additional notes:**

1. The validation file currently does not use a discard file.

**Example:**

::

    <Validation>
    <Environment>
        <Verbfile>PETR.Validate.verbs.txt</Verbfile>
        <Actorfile>PETR.Validate.actors.txt</Actorfile>
        <Agentfile>PETR.Validate.agents.txt</Agentfile>
        <Errorfile>Errors.unit-test.txt</Errorfile>
        <Include>valid DEMO ACTOR VERB AGENT COMPOUND PARSING PATTERN DATE MODIFY SYNSET</Include>
        <Pause>Stop</Pause>
        <Config option="stop_on_error" value="True"></Config>
    </Environment>		
    <Sentences>
    <Sentence date="19950101" id="DEMO-01" category="DEMO">
    <!-- [Simple coding] -->
    <EventCoding sourcecode="ARN" targetcode="GON" eventcode="064">
    <Text>
    Arnor is about to restore full diplomatic ties with Gondor almost
    five years after crowds trashed its embassy, a senior official
    said on Saturday.
    </Text>
    <Parse>
    (ROOT
        (S
            (S
                (NP (NNP Arnor))
                (VP (VBZ is)
                    (VP (IN about)
                        (S
                            (VP (TO to)
                                (VP (VB restore)
                                    (NP (JJ full) (JJ diplomatic) (NNS ties))
                                    (PP (IN with)
                                        (NP (NNP Gondor)))
                                    (SBAR
                                        (NP (RB almost) (CD five) (NNS years))
                                        (IN after)
                                        (S
                                            (NP (NNS crowds))
                                            (VP (VBD trashed)
                                                (NP (PRP$ its) (NN embassy)))))))))))
            (, ,)
            (NP (DT a) (JJ senior) (NN official))
            (VP (VBD said)
                (PP (IN on)
                    (NP (NNP Saturday))))
            (. .)))
    </Parse>
    </Sentence>
    </Sentences>
    </Validation>
