from petrarch import petrarch, PETRglobals, PETRreader, utilities
from petrarch import PETRtree as ptree


config = petrarch.utilities._get_data('data/config/', 'PETR_config.ini')
print("reading config")
petrarch.PETRreader.parse_Config(config)
print("reading dicts")
petrarch.read_dictionaries()




def test_version():
    assert petrarch.get_version() == "1.0.0"


def test_read():
    assert "RUSSIA" in PETRglobals.ActorDict



###################################
#
#       Full sentence tests
#
###################################

def test_simple():
    text = "Germany invaded France"
    parse = "(ROOT (S (NP (NNP Germany)) (VP (VBD invaded) (NP (NNP France)))))"
    parsed = utilities._format_parsed_str(parse)
    
    dict = {u'test123': {u'sents': {u'0': {u'content': text, u'parsed': parsed}},
                u'meta': {u'date': u'20010101'}}}

    return_dict = petrarch.do_coding(dict,None)
    print(return_dict)
    assert return_dict['test123']['sents']['0']['events'] == [['DEU','FRA','192']]


def test_simple2():
    text = "Germany arrested France"
    parse = "(ROOT (S (NP (NNP Germany)) (VP (VBD arrested) (NP (NNP France)))))"
    parsed = utilities._format_parsed_str(parse)

    dict = {u'test123': {u'sents': {u'0': {u'content': text, u'parsed': parsed}},
                u'meta': {u'date': u'20010101'}}}

    return_dict = petrarch.do_coding(dict,None)
    print(return_dict)
    assert return_dict['test123']['sents']['0']['events'] == [['DEU','FRA','173']]



def test_complex1():

    text = "A Tunisian court has jailed a Nigerian student for two years for helping young militants join an armed Islamic group in Lebanon, his lawyer said Wednesday."

    parse = """( (S (S
    (NP (DT A) (NNP Tunisian) (NN court))
    (VP (AUXZ has)
    (VP (VBN jailed)
    (NP (DT a) (JJ Nigerian) (NN student))
    (PP (IN for)
    (NP (CD two) (NNS years)))
    (PP (IN for) (S
    (VP (VBG helping) (S
    (NP (JJ young) (NNS militants))
    (VP (VB join)
    (NP (NP (DT an) (JJ armed) (JJ Islamic) (NN group))
    (PP (IN in)
    (NP (NNP Lebanon)))))))))))) (, ,)
    (NP (PRP$ his) (NN lawyer))
    (VP (VBD said)
    (NP (NNP Wednesday))) (. .)))"""


    parsed = utilities._format_parsed_str(parse)

    dict = {u'test123': {u'sents': {u'0': {u'content': text, u'parsed': parsed}},
                u'meta': {u'date': u'20010101'}}}

    return_dict = petrarch.do_coding(dict,None)
    assert return_dict['test123']['sents']['0']['events'] == [['TUNJUD','NGAEDU','173']]


###################################
#
#           Unit tests
#
#   note : Even though most of these
#          are phrasal tests, the
#          tree needs to be S-rooted
#          for it to read correctly
#
###################################

def test_noun_meaning1():
    parse = "(S (NP (DT THE ) (JJ ISLAMIC ) (NN STATE ) ) "

    test = ptree.Sentence(parse,"The Islamic State", "081315")

    phrase = test.tree.children[0]

    head, headphrase = phrase.get_head()
    
    assert head== "STATE"
    
    assert headphrase == phrase
    
    assert phrase.get_meaning() == ["IMGMUSISI"]


def test_noun_meaning2():
    parse = "(S (NP (DT THE ) (JJ NORTH ) (NN ATLANTIC ) (NN TREATY ) (NN ORGANIZATION ) ) )  "

    test = ptree.Sentence(parse,"The North Atlantic Treaty Organization", "081315")

    phrase = test.tree.children[0]

    head, headphrase = phrase.get_head()
    
    assert head== "ORGANIZATION"
    
    assert headphrase == phrase
    
    assert phrase.get_meaning() == ["IGOWSTNAT"]


def test_noun_meaning3():
    parse = "(S (NP (NP (NNP BARACK ) (NNP OBAMA ) ) (CC AND ) (NP (NNP VLADIMIR ) (NNP PUTIN ) ) ) )"

    test = ptree.Sentence(parse,"Barack Obama and Vladimir Putin", "081315")

    phrase = test.tree.children[0]
    
    assert sorted(phrase.get_meaning()) == sorted(["USAGOV","RUSELI"])


def test_prepmeaning():
    parse = "(S (PP (IN TO ) (NP (DT THE ) (JJ TURKISH ) (NN MARKET )  ) ) )"

    test = ptree.Sentence(parse,"to the market", "081315")

    phrase = test.tree.children[0]
    
    assert phrase.get_meaning() == ['TUR']

    assert phrase.head == "MARKET"

    assert phrase.get_prep() == "TO"



def test_noun_meaning4():
    parse = "(S (NP (DT THE ) (NNP REBELS ) (PP (IN FROM ) (NP (NNP SYRIA ) ) ) ) )"

    test = ptree.Sentence(parse,"The rebels from Syria", "081315")

    phrase = test.tree.children[0]
    
    assert phrase.get_meaning() == ['SYRREB']

    assert phrase.get_head()[0] == "REBELS"

    assert phrase.get_head()[1] == phrase








