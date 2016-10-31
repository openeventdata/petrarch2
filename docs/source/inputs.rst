Input Formats
=============

There are two input formats for PETRARCH: the processing
pipeline and the XML input. The following
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
`relevant documentation <modules.html#PETRwriter.pipe_output>`_.

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

