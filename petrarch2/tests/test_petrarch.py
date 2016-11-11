from petrarch2 import petrarch2, PETRglobals, PETRreader, utilities
from petrarch2 import PETRtree as ptree
import sys


config = petrarch2.utilities._get_data('data/config/', 'PETR_config.ini')
print("reading config")
sys.stdout.write('Mk1\n')
petrarch2.PETRreader.parse_Config(config)
print("reading dicts")
petrarch2.read_dictionaries()




def test_version():
    assert petrarch2.get_version() == "1.2.0"


def test_read():
    assert "RUSSIA" in PETRglobals.ActorDict

def test_actorDict_read():
    #actorDict1 is an example that "CROATIA" appears multiple times in the dictionary, we should store all codes
    actorDict1 = {u'#': [(u'YUGHRV', [u'<910625']), (u'HRVUNR', [u'911008', u'920115']), (u'HRV', [u'>920115']), (u'HRV', [])]}
    
    #actorDict2 is an example of multiple codes in one line
    #UFFE_ELLEMANN_JENSEN_ [IGOEUREEC 820701-821231][IGOEUREEC 870701-871231] # president of the CoEU 
    actorDict2 = {u'ELLEMANN': {u'JENSEN': {u'#': [(u'IGOEUREEC', [u'820701', u'821231']), (u'IGOEUREEC', [u'870701', u'871231'])]}}}
    
    #actorDict3 is an example of extra space in the date
    #+EL_SISI_
    #[EGYMIL 770101-120812]
    #[EGYGOVMIL 120812-140326]
    #[EGYGOV > 140608]
    #[EGYELI]
    actorDict3 = {u'#': [(u'EGYMIL', [u'770101', u'120812']), (u'EGYGOVMIL', [u'120812', u'140326']), (u'EGYGOV', [u'>140608']), (u'EGYELI', [])]}

    #actorDict4-6 are examples that phrase and code is separated by different whitespace characters
    actorDict4 = {u'HARAM': {u'#': [(u'NGAREB', [])]}} #one space
    actorDict5 = {u'INC': {u'#': [(u'MNCUSA', [])]}} #two space
    actorDict6 = {u'#': [(u'KIR', [])]} #one tab

    assert PETRglobals.ActorDict['CROATIA'] == actorDict1
    assert PETRglobals.ActorDict['UFFE'] == actorDict2
    assert PETRglobals.ActorDict['EL']['SISI'] == actorDict3
    assert PETRglobals.ActorDict['BOKO'] == actorDict4
    assert PETRglobals.ActorDict['SOLARWINDS'] == actorDict5
    assert PETRglobals.ActorDict['KIRIBATI'] == actorDict6


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

    assert sorted(phrase.get_meaning()) == sorted(["USAGOV","RUSGOV"])


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

def test_noun_meaning5():
    parse = "(S (NP (NP (DT THE ) (NNP US ) (NN COMMANDER ) ) (PP (IN IN ) (NP (NNP IRAQ ) ) ) ) )"

    test = ptree.Sentence(parse,"The US commander in Iraq", "081315")

    phrase = test.tree.children[0]
    test.tree.print_to_stdout("")
    assert phrase.get_meaning() == ['USAMIL']
    assert phrase.get_head()[0] == "COMMANDER"

def test_date_check():
    parse = "(S (NP (NNP CARL ) (NN XVI ) (NNP GUSTAF ) ) )"

    test = ptree.Sentence(parse,"Carl XVI Gustaf", PETRreader.dstr_to_ordate("20150813"))
    phrase = test.tree.children[0]
    assert phrase.get_meaning() == ["SWEGOV"]

    test = ptree.Sentence(parse,"Carl XVI Gustaf", PETRreader.dstr_to_ordate( "19720813"))
    phrase = test.tree.children[0]
    assert phrase.get_meaning() == ["SWEELI"]

    test = ptree.Sentence(parse,"Carl XVI Gustaf", PETRreader.dstr_to_ordate("19010813"))
    phrase = test.tree.children[0]
    assert phrase.get_meaning() == ["SWEELI"]


def test_personal1():
    parse = "(S (NP (NNP Obama ) ) (VP (VBD said ) (SBAR (S (NP (PRP he ) ) (VP (VBD was ) (ADJP (VBN tired ) ) ) ) ) ) ) ".upper()

    print('This is a test')
    test = ptree.Sentence(parse,"Obama said he was tired",PETRreader.dstr_to_ordate("20150813"))
    phrase = test.tree.children[1].children[1].children[0].children[0]
    assert phrase.get_meaning() == ["USAGOV"]


def test_reflexive():
    parse = "(S (NP (NNP Obama ) )  (VP (VBD asked ) (NP (PRP himself ) )  (SBAR (WHADVP (WRB why ) ) (S (NP (NNP Biden ) ) (VP (VBD was ) (ADJP (VBN tired ) ) ) ) ) ) )".upper()

    test = ptree.Sentence(parse,"Obama asked himself why Biden was tired",PETRreader.dstr_to_ordate("20150813"))
    phrase = test.tree.children[1].children[1]
    assert phrase.get_meaning() == ["USAGOV"]


def test_personal2():
    parse = "(S (NP (NNP Obama ) ) (VP (VBD knew ) (SBAR (IN that ) (S (NP (NNP Biden ) ) (VP (VBD liked ) (NP (PRP him ) ) ) ) ) )  ) ".upper()

    test = ptree.Sentence(parse,"Obama knew that Biden liked him",PETRreader.dstr_to_ordate("20150813"))
    phrase = test.tree.children[1].children[1].children[1].children[1].children[1]
    assert phrase.get_meaning() == ["USAGOV"]


def test_reflexive2():
    parse = "(S (NP (NNP Obama ) ) (VP (VBD knew ) (SBAR (IN that ) (S (NP (NNP Putin ) ) (VP (VBD liked ) (NP (PRP himself ) ) ) ) ) )  ) ".upper()

    test = ptree.Sentence(parse,"Obama knew that Biden liked him",PETRreader.dstr_to_ordate("20150813"))
    phrase = test.tree.children[1].children[1].children[1].children[1].children[1]
    assert phrase.get_meaning() == ["RUSGOV"]


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

    return_dict = petrarch2.do_coding(dict)
    print(return_dict)
    assert return_dict['test123']['sents']['0']['events'] == [('DEU','FRA','192')]


def test_simple2():
    text = "Germany arrested France"
    parse = "(ROOT (S (NP (NNP Germany)) (VP (VBD arrested) (NP (NNP France)))))"
    parsed = utilities._format_parsed_str(parse)

    dict = {u'test123': {u'sents': {u'0': {u'content': text, u'parsed': parsed}},
                u'meta': {u'date': u'20010101'}}}

    return_dict = petrarch2.do_coding(dict)
    print(return_dict)
    assert return_dict['test123']['sents']['0']['events'] == [('DEU','FRA','173')]


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
    (NP (NP (DT an) (JJ armed) (JJ Islamic) (NN group))f
    (PP (IN in)
    (NP (NNP Lebanon)))))))))))) (, ,)
    (NP (PRP$ his) (NN lawyer))
    (VP (VBD said)
    (NP (NNP Wednesday))) (. .)))"""


    parsed = utilities._format_parsed_str(parse)

    dict = {u'test123': {u'sents': {u'0': {u'content': text, u'parsed': parsed}},
                u'meta': {u'date': u'20010101'}}}
    return_dict = petrarch2.do_coding(dict)
    print(return_dict)
    assert return_dict['test123']['sents']['0']['events'] == [('TUNJUD','NGAEDU','173')]








