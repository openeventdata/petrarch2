# -*- coding: utf-8 -*-

##	utilities.py [module]
##
# Utilities for the PETRARCH event data coder
##
# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.10; it is standard Python 2.7
# so it should also run in Unix or Windows.
#
# INITIAL PROVENANCE:
# Programmer:
#             John Beieler
#			  Caerus Associates/Penn State University
#			  Washington, DC / State College, PA, 16801 U.S.A.
#			  http://caerusassociates.com
#             http://bdss.psu.edu
#
# GitHub repository: https://github.com/openeventdata/petrarch
#
# Copyright (c) 2014	John Beieler.	All rights reserved.
#
# This project is part of the Open Event Data Alliance tool set
#
# This code is covered under the MIT license
#
# Report bugs to: john.b30@gmail.com
#
# REVISION HISTORY:
#    Summer-14:	 Initial version
#    April 2016: added extract_phrases() 

# pas 16.04.22: print() statements commented-out with '# --' were used in the debugging and can probably be removed
# ------------------------------------------------------------------------


from __future__ import print_function
from __future__ import unicode_literals

import os
import logging
#import corenlp
import dateutil.parser
import PETRglobals
from collections import defaultdict, Counter



# Deprecated. Use hypnos instead.
# def stanford_parse(event_dict):
#     logger = logging.getLogger('petr_log')
#     # What is dead can never die...
#     print("\nSetting up StanfordNLP. The program isn't dead. Promise.")
#     logger.info('Setting up StanfordNLP')
#     core = corenlp.StanfordCoreNLP(PETRglobals.stanfordnlp,
#                                    properties=_get_data('data/config/',
#                                                         'petrarch.properties'),
#                                    memory='2g')
#     total = len(list(event_dict.keys()))
#     print(
#         "Stanford setup complete. Starting parse of {} stories...".format(total))
#     logger.info(
#         'Stanford setup complete. Starting parse of {} stories.'.format(total))
#     for i, key in enumerate(event_dict.keys()):
#         if (i / float(total)) * 100 in [10.0, 25.0, 50, 75.0]:
#             print('Parse is {}% complete...'.format((i / float(total)) * 100))
#         for sent in event_dict[key]['sents']:
#             logger.info('StanfordNLP parsing {}_{}...'.format(key, sent))
#             sent_dict = event_dict[key]['sents'][sent]
#
#             if len(sent_dict['content']) > 512 or len(
#                     sent_dict['content']) < 64:
#                 logger.warning(
#                     '\tText length wrong. Either too long or too short.')
#                 pass
#             else:
#                 try:
#                     stanford_result = core.raw_parse(sent_dict['content'])
#                     s_parsetree = stanford_result['sentences'][0]['parsetree']
#                     if 'coref' in stanford_result:
#                         sent_dict['coref'] = stanford_result['coref']
#
#                     # TODO: To go backwards you'd do str.replace(' ) ', ')')
#                     sent_dict['parsed'] = _format_parsed_str(s_parsetree)
#                 except Exception as e:
#                     print('Something went wrong. ¯\_(ツ)_/¯. See log file.')
#                     logger.warning(
#                         'Error on {}_{}. ¯\_(ツ)_/¯. {}'.format(key, sent, e))
#     print('Done with StanfordNLP parse...\n\n')
#     logger.info('Done with StanfordNLP parse.')
#
#     return event_dict



def parse_to_text(parse):
    x = filter(lambda a : not a.startswith("("), parse.replace(")","").split())
    r = "" + x[0]
    for item in x[1:]:
        r += " " + item
    return r


def extract_phrases(sent_dict,sent_id):
    """  
    Text extraction for PETRglobals.WriteActorText and PETRglobals.WriteEventText 

    Parameters
    ----------

    story_dict: Dictionary.
                Story-level dictionary as stored in the main event-holding dictionary within PETRARCH.

    story_id: String.
                Unique StoryID in standard PETRARCH format.

    Returns
    -------

    text_dict: Dictionary indexed by event 3-tuple.
               List of texts in the order  [source_actor, target_actor, event]
    """

    def get_text_phrase(phst):
        """ find the words in original sentence text corresponding to the string phst, putting in ... when the words
            are not consecutive and < wd > for elements not recognized, which are usually actor codes or synonym sets. """
        phlist = phst.split(' ')  
        curloc = 0
        lcphst = ''
        for wd in phlist:
            newloc = ucont.find(wd,curloc)
            if newloc >= 0:
                if lcphst and newloc > curloc + 1: # add elipses if words are not consecutive
                    lcphst += ' ...'
                curloc = newloc + len(wd)
                lcphst += ' ' + content[newloc:curloc]
            else:
                lcphst += ' <' + wd + '>'  # use <...> for elements not recognized
# --        print('   GTP:',lcphst)
        return lcphst.strip()    
    
    def get_noun_list():
        """ Make (text, code, root) tuples from any sets of compounds """
# --        print('gnl: ',sent_dict['meta']['nouns'])
        noun_list = []
        for ca in sent_dict['meta']['nouns']:  # 
            if len(ca[1]) == 1:
                noun_list.append(ca)
            else:
                for ka in range(len(ca[1])):
                    #noun_list.append((ca[0][ka],ca[1][ka],ca[2][ka]))
                    if ka < len(ca[0]):   
                        noun_list.append((ca[0][ka],ca[1][ka],ca[2][ka]))
                    else:
                        noun_list.append((ca[0][-1],ca[1][ka],ca[2][-1]))  # appears this can occur if the same string, e.g. "MINISTER" applies to multiple codes
                    
        return noun_list                                 

    def get_actor_phrase(code,typest):
        if code.startswith('---'):
            code = '~' + code[3:]
        noun_list = get_noun_list()
                                            
# --        print(' -- ',noun_list)
        for ca in noun_list:
            if code in ca[1]:
# --                print(' -- match:',code, ca)
                tarst = ''
                for st in ca[0]:
                    tarst += st
# --                print(typest + ' text:',tarst)
                return get_text_phrase(tarst[1:])
        else:
            logger.info('ut.EP {} text not found'.format(sent_id, typest))
            print('ut.EP {} text not found'.format(sent_id, typest))
            return '---'

    def get_actor_root(code):
        if code.startswith('---'):
            return '---'
        noun_list = get_noun_list()                                            
# --        print(' ** ',noun_list)
        for ca in noun_list:
# --            print('===',ca)  # --
            if code in ca[1]:
# --                print(' -- match:',code, ca)   # --
                if len(ca) > 2 and ca[2] != '~':
                        phrst = ''
                        for li in ca[2]:
                            if isinstance(li,list):  # 16.04.28 pas I am not happy with this contigency: things should be stored in just one format, but don't have time to resolve this at the moment
                                phrst += ' ' + ' '.join(li)
                            else:
                                phrst += ' ' + li
                                                    
                        return phrst.replace(' ~','').strip()
                        
                else:
# --                    print(' -- -- \'---\'')
                    return '---'
        else:
            return '---'

    def get_event_phrase(verb_list):
        phst = ''
        words = ''
        for st in verb_list:
# --            print('   GEP1:',st)
            if isinstance(st,basestring):  # handles those  ~ a (a b Q) SAY = a b Q cases I haven't figured out yet [pas 16.04.20]
                continue
            if len(st) > 1:
                if '[' in st[1]:  # create a phrase for a pattern
                    sta = st[1][1:st[1].find('[')].strip()
                    words = sta.replace('*',st[0])
                    words = words.replace('(','')
                    words = words.replace(')','')
                elif isinstance(st[1],tuple):   # create phrase based on a tuple patterns
                    words = st[0]
                    for tp in st[1:]:
                        words += ' ' + tp[0] 
                        if len(tp[1]) > 0:
                            words += ' ' + tp[1][0]
                        else:
                            words += ' ---'
                else:
                    words = str(st)
            else:
                if st[0]:   # in very rare circumstances, st[0] == None
                    words = st[0]
            if words not in phst:  # 16.04.28: verbs are occasionally duplicated in 'meta' -- this is just a hack to get around that at the moment
                phst = words + ' ' + phst
# --            print('   GEP2:',phst)
        return get_text_phrase(phst)
               
    logger = logging.getLogger('petr_log')
    text_dict = {}  # returns texts in lists indexed by evt
    """print('EP1:',sent_dict['content']) # --
    print('EP2:',sent_dict['meta'])  # -- """
    content = sent_dict['content']
    ucont = sent_dict['content'].upper()
    keylist = list(sent_dict['meta'].keys())
    if len(keylist) < 2:
        logger.info('ut.EP {} len(keylist) < 2 {}'.format(sent_id, keylist))
        print('ut.EP {} len(keylist) < 2 {}'.format(sent_id, keylist))
    for evt in keylist:
        if evt == 'nouns':
            continue
# --        print('EP3:',evt)
        text_dict[evt] = ['','','','','']
        if PETRglobals.WriteActorText :
            text_dict[evt][0] = get_actor_phrase(evt[0],'Source')
            text_dict[evt][1] = get_actor_phrase(evt[1],'Target')
        if PETRglobals.WriteEventText :
            text_dict[evt][2] = get_event_phrase(sent_dict['meta'][evt])
        if PETRglobals.WriteActorRoot :
            text_dict[evt][3] = get_actor_root(evt[0]) # 'SRC-ROOT' 
            text_dict[evt][4] = get_actor_root(evt[1]) # 'TAR-ROOT'
    return text_dict

def story_filter(story_dict, story_id):
    """
    One-a-story filter for the events. There can only be only one unique
    (DATE, SRC, TGT, EVENT) tuple per story.

    Parameters
    ----------

    story_dict: Dictionary.
                Story-level dictionary as stored in the main event-holding
                dictionary within PETRARCH.

    story_id: String.
                Unique StoryID in standard PETRARCH format.

    Returns
    -------

    filtered: Dictionary.
                Holder for filtered events with the format
                {(EVENT TUPLE): {'issues': [], 'ids': []}} where the 'issues'
                list is optional.
    """
    filtered = defaultdict(dict)
    story_date = story_dict['meta']['date']
    for sent in story_dict['sents']:
        sent_dict = story_dict['sents'][sent]
        sent_id = '{}_{}'.format(story_id, sent)
        if 'events' in sent_dict:
            """print('ut:SF1',sent,'\n',story_dict['sents'][sent])
            print('ut:SF2: ',story_dict['meta'])
            print('ut:SF3: ',story_dict['sents'][sent]['meta'])
            print('ut:SF4: ',story_dict['sents'][sent]['events'])"""
            """if  PETRglobals.WriteActorText or PETRglobals.WriteEventText:  # this is the old call before this was moved out to do_coding()
                text_dict = extract_phrases(story_dict['sents'][sent],sent_id)
            else:
                text_dict = {}"""

            for event in story_dict['sents'][sent]['events']:
                # do not print unresolved agents
                try:
                    alist = [story_date]
                    alist.extend(event)
                    event_tuple = tuple(alist)
                    filtered[event_tuple]
                    if 'issues' in sent_dict:
                        filtered[event_tuple]['issues'] = Counter()
                        issues = sent_dict['issues']
                        for issue in issues:
                            filtered[event_tuple]['issues'][
                                issue[0]] += issue[1]

                    # Will keep track of this info, but not necessarily write it out
                    filtered[event_tuple]['ids'] = []
                    filtered[event_tuple]['ids'].append(sent_id)
#                    if event_tuple[1:] in text_dict:  # log an error here if we can't find a non-null case?
                    if 'actortext' in sent_dict['meta'] and event_tuple[1:] in sent_dict['meta']['actortext']:  # 16.04.29 this is a revised version of the above test: it catches cases where extract_phrases() returns a null
                        if PETRglobals.WriteActorText :
                            filtered[event_tuple]['actortext'] = sent_dict['meta']['actortext'][event_tuple[1:]]
                        if PETRglobals.WriteEventText :
                            filtered[event_tuple]['eventtext'] = sent_dict['meta']['eventtext'][event_tuple[1:]]
                        if PETRglobals.WriteActorRoot :
                            filtered[event_tuple]['actorroot'] = sent_dict['meta']['actorroot'][event_tuple[1:]]

                except IndexError:  # 16.04.29 pas it would be helpful to log an error here...
                    pass
        else:
            pass

    return filtered


def _format_parsed_str(parsed_str):
    if parsed_str.strip().startswith("(ROOT") and parsed_str.strip().endswith(")"):
        parsed_str = parsed_str.strip()[5:-1].strip()
    elif parsed_str.strip()[1:].strip().startswith("("):
        parsed_str = parsed_str.strip()[1:-1]
    parsed = parsed_str.split('\n')
    parsed = [line.strip() + ' ' for line in [line1.strip() for line1 in
                                              parsed if line1] if line]
    parsed = [line.replace(')', ' ) ').upper() for line in parsed]
    treestr = ''.join(parsed)
    return treestr


def _format_datestr(date):
    datetime = dateutil.parser.parse(date)
    date = '{}{:02}{:02}'.format(datetime.year, datetime.month, datetime.day)
    return date


def _get_data(dir_path, path):
    """Private function to get the absolute path to the installed files."""
    cwd = os.path.abspath(os.path.dirname(__file__))
    joined = os.path.join(dir_path, path)
    out_dir = os.path.join(cwd, joined)
    return out_dir


def _get_config(config_name):
    cwd = os.path.abspath(os.path.dirname(__file__))
    out_dir = os.path.join(cwd, config_name)
    return out_dir


def init_logger(logger_filename):

    logger = logging.getLogger('petr_log')
    logger.setLevel(logging.INFO)

    cwd = os.getcwd()
    logger_filepath = os.path.join(cwd, logger_filename)

    fh = logging.FileHandler(logger_filepath, 'w')
    formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('Running')



def combine_code(selfcode,to_add):
    """
    Combines two verb codes, part of the verb interaction framework


    Parameters
    ----------
    selfcode,to_add: ints
                     Upper and lower verb codes, respectively

    Returns
    -------
    combined value

    """

    if to_add < 0:
        return to_add + selfcode
    if selfcode >= 0x1000 and to_add >= 0x1000:
        return to_add  # If both verbs are high-level, take the lower nested one. I think this is what we want?
    if to_add >= selfcode:
        return to_add

    return selfcode + to_add



def code_to_string(events):
    """
    Converts an event into a string, replacing the integer codes with strings
    representing their value in hex
    """
    retstr= ""
    try:
        def ev_to_string(ev):
            local = ""
            if isinstance(ev,basestring):
                return ev
            up = str(ev[0])
            low = ev[1]
            c = ev[2]

            if isinstance(low,tuple):
                low = "("+ev_to_string(low)+")"

            return up + " " + low + " " + hex(c)
        for ev in events:
            #print(ev)
            retstr += ev_to_string(ev) +" , "

        return retstr[:-3]

    except Exception as e:
        print(e)
        return str(events)




def convert_code(code,forward = 1):
    """
    Convert a verb code between CAMEO and the Petrarch internal coding ontology.

                New coding scheme:

            0                0          0                       0
            2 Appeal         1 Reduce   1 Meet                  1 Leadership
            3 Intend         2 Yield    2 Settle                2 Policy
            4 Demand                    3 Mediate               3 Rights
            5 Protest                   4 Aid                   4 Regime
            6 Threaten	                5 Expel                 5 Econ
            1 Say                       6 Pol. Change           6 Military
            7 Disapprove                7 Mat. Coop             7 Humanitarian
            8 Posture                   8 Dip. Coop             8 Judicial
            9 Coerce                    9 Assault	            9 Peacekeeping
            A Investigate               A Fight		        	A Intelligence
            B Consult  		       		B Mass violence			B Admin. Sanctions
            						    			            C Dissent
            						    				        D Release
            							     		            E Int'l Involvement
            						   						    F D-escalation

    In the first column, higher numbers take priority. i.e. “Say + Intend” is just “Intend” or “Intend + Consult” is just Consult


    Parameters
    ----------
    code: string or int, depending on forward
          Code to be converted

    forward: boolean
             Direction of conversion, True = CAMEO -> PICO


    Returns
    -------
    Forward mode:
        active, passive : int
                          The two parts of the code [XXX:XXX], converted to the new system. The first is an inherent
                          active meaning, the second is an inherent passive meaning. Both are not always present,
                          most codes just have the active.

    """


    cat = {             "010"    :     0x1000 ,         #  Make Public Statement
                        "011"    :     0x1000 - 0xFFFF ,
                        "012"    :     0x100C  ,
                        "013"    :     0x1001  ,
                        "014"    :     0x1002  ,
                        "015"    :     0x10a0  ,
                        "016"    :     0x10a0 - 0xFFFF ,
                        "017"    :     0x1003  ,
                        "018"    :     0x1004  ,
                        "019"    :     0x1005  ,


                        "020"    :     0x2000  ,         #  Appeal
                        "021"    :     0x2070  ,
                        "0211"   :     0x2075  ,
                        "0212"   :     0x2076  ,
                        "0213"   :     0x2078  ,
                        "0214"   :     0x207A  ,
                        "022"    :     0x2080  ,
                        "023"    :     0x2040  ,
                        "0231"   :     0x2045  ,
                        "0232"   :     0x2046  ,
                        "0233"   :     0x2047  ,
                        "0234"   :     0x2049  ,
                        "024"    :     0x2060  ,
                        "0241"   :     0x2061  ,
                        "0242"   :     0x2062  ,
                        "0243"   :     0x2063  ,
                        "0244"   :     0x2064  ,
                        "025"    :     0x2200  ,
                        "0251"   :     0x220B  ,
                        "0252"   :     0x220C  ,
                        "0253"   :     0x220D  ,
                        "0254"   :     0x2205  ,
                        "0255"   :     0x220E  ,
                        "0256"   :     0x220F  ,
                        "026"    :     0x2010  ,
                        "027"    :     0x2020  ,
                        "028"    :     0x2030  ,


                        "030"    :     0x3000  ,         #  Intend
                        "031"    :     0x3070  ,
                        "0311"   :     0x3075  ,
                        "0312"   :     0x3076  ,
                        "0313"   :     0x3078  ,
                        "0314"   :     0x307A  ,
                        "032"    :     0x3080  ,
                        "033"    :     0x3040  ,
                        "0331"   :     0x3045  ,
                        "0332"   :     0x3046  ,
                        "0333"   :     0x3047  ,
                        "0334"   :     0x3049  ,
                        "034"    :     0x3060  ,
                        "0341"   :     0x3061  ,
                        "0342"   :     0x3062  ,
                        "0343"   :     0x3063  ,
                        "0344"   :     0x3064  ,
                        "035"    :     0x3200  ,
                        "0351"   :     0x320B  ,
                        "0352"   :     0x320C  ,
                        "0353"   :     0x320D  ,
                        "0354"   :     0x3205  ,
                        "0355"   :     0x320E  ,
                        "0356"   :     0x320F  ,
                        "036"    :     0x3010  ,
                        "037"    :     0x3020  ,
                        "038"    :     0x3230  ,
                        "039"    :     0x3030  ,

                        "040"    :     0xB000  ,         #  Consult
                        "041"    :     0xB001  ,
                        "042"    :     0xB002  ,
                        "043"    :     0xB003  ,
                        "044"    :     0xB010  ,
                        "045"    :     0xB030  ,
                        "046"    :     0xB010  ,


                        "050"    :     0x0080   ,        # Diplomatic Coop
                        "051"    :     0x0081   ,
                        "052"    :     0x0082   ,
                        "053"    :     0x0083   ,
                        "054"    :     0x0084   ,
                        "055"    :     0x0085   ,
                        "056"    :     0x0086   ,
                        "057"    :     0x0087   ,

                        "060"    :     0x0070   ,        # Material Coop
                        "061"    :     0x0075   ,
                        "062"    :     0x0076   ,
                        "063"    :     0x0078   ,
                        "064"    :     0x007A   ,

                        "070"    :     0x0040   ,        # Provide Aid
                        "071"    :     0x0045   ,
                        "072"    :     0x0046   ,
                        "073"    :     0x0047   ,
                        "074"    :     0x0049   ,
                        "075"    :     0x004E   ,

                        "080"    :     0x0200  ,         #  Yield
                        "081"    :     0x020B  ,
                        "0811"   :     0x0203  ,
                        "0812"   :     0x0201  ,
                        "0813"   :     0x0204  ,
                        "0814"   :     0x0206  ,
                        "082"    :     0x020C  ,
                        "083"    :     0x0260  ,
                        "0831"   :     0x0261  ,
                        "0832"   :     0x0262  ,
                        "0833"   :     0x0263  ,
                        "0834"   :     0x0264  ,
                        "084"    :     0x0250  ,
                        "0841"   :     0x020C  ,
                        "0842"   :     0x020C  ,
                        "085"    :     0x0205  ,
                        "086"    :     0x020E  ,
                        "0861"   :     0x0209  ,
                        "0862"   :     0x020A  ,
                        "0863"   :     0x0207  ,
                        "087"    :     0x02C0  ,
                        "0871"   :     0x02C9  ,
                        "0872"   :     0x02C1  ,
                        "0873"   :     0x02C6  ,
                        "0874"   :     0x02C2  ,
                        "08"     :     0x0200  ,

                        "090"    :     0xA000  ,         #  Investigate
                        "091"    :     0xA001  ,
                        "092"    :     0xA002  ,
                        "093"    :     0xA003  ,
                        "094"    :     0xA004  ,

                        "100"    :     0x4000  ,         #  Demand
                        "101"    :     0x4070  ,
                        "1011"   :     0x4075  ,
                        "1012"   :     0x4076  ,
                        "1013"   :     0x4078  ,
                        "1014"   :     0x407A  ,
                        "102"    :     0x4080  ,
                        "103"    :     0x4040  ,
                        "1031"   :     0x4045  ,
                        "1032"   :     0x4046  ,
                        "1033"   :     0x4047  ,
                        "1034"   :     0x4049  ,
                        "104"    :     0x4060  ,
                        "1041"   :     0x4061  ,
                        "1042"   :     0x4062  ,
                        "1043"   :     0x4063  ,
                        "1044"   :     0x4064  ,
                        "105"    :     0x4200  ,
                        "1051"   :     0x420B  ,
                        "1052"   :     0x420C  ,
                        "1053"   :     0x420D  ,
                        "1054"   :     0x4205  ,
                        "1055"   :     0x420E  ,
                        "1056"   :     0x420F  ,
                        "106"    :     0x4010  ,
                        "107"    :     0x4020  ,
                        "108"    :     0x4030  ,


                        "110"    :     0x7000  ,         #  Disapprove
                        "111"    :     0x7001  ,
                        "112"    :     0x70a0  ,
                        "1121"   :     0x70a1  ,
                        "1122"   :     0x70a2  ,
                        "1123"   :     0x70a3  ,
                        "1124"   :     0x70a4  ,
                        "1125"   :     0x70a5  ,
                        "113"    :     0x7002  ,
                        "114"    :     0x7003  ,
                        "115"    :     0x7008  ,
                        "116"    :     0x7005  ,


                        "120"    :   -0xFFFF   ,         #  Reject
                        "121"    :   -0xFFFF + 0x0070 ,
                        "1211"   :   -0xFFFF + 0x0075 ,
                        "1212"   :   -0xFFFF + 0x0076 ,
                        "122"    :   -0xFFFF + 0x2040 + 0x300 ,      # The 0x300 mask makes these not code
                        "1221"   :   -0xFFFF + 0x2045 + 0x300,       # from "refuse to request aid", but rather
                        "1222"   :   -0xFFFF + 0x2046 + 0x300,       # be a thing of their own while retaining
                        "1223"   :   -0xFFFF + 0x2047 + 0x300,       # the features of the meaning.
                        "1224"   :   -0xFFFF + 0x2049 + 0x300,
                        "123"    :   -0xFFFF + 0x2060 + 0x300,
                        "1231"   :   -0xFFFF + 0x2061 + 0x300,
                        "1232"   :   -0xFFFF + 0x2062 + 0x300,
                        "1233"   :   -0xFFFF + 0x2063 + 0x300,
                        "1234"   :   -0xFFFF + 0x2064 + 0x300,
                        "124"    :   -0xFFFF + 0x0200 ,
                        "1241"   :   -0xFFFF + 0x020B ,
                        "1242"   :   -0xFFFF + 0x020C ,
                        "1243"   :   -0xFFFF + 0x020D ,
                        "1244"   :   -0xFFFF + 0x0205 ,
                        "1245"   :   -0xFFFF + 0x020E ,
                        "1246"   :   -0xFFFF + 0x02C0 ,
                        "125"    :   -0xFFFF + 0x0010 ,
                        "126"    :   -0xFFFF + 0x0030 ,
                        "127"    :   -0xFFFF + 0x0020 ,
                        "128"    :   -0xFFFF + 0x0002 ,
                        "129"    :   -0xFFFF + 0x0001 ,

                        "130"    :     0x6000  ,         #  Threaten
                        "131"    :     0x6100 ,
                        "1311"   :     0x6140  ,
                        "1312"   :     0x6105  ,
                        "1313"   :     0x6180  ,
                        "132"    :     0x600B  ,
                        "1321"   :     0x6003  ,
                        "1322"   :     0x6001  ,
                        "1323"   :     0x6004  ,
                        "1324"   :     0x6006  ,
                        "133"    :     0x600C  ,
                        "134"    :     0x6010  ,
                        "135"    :     0x6030  ,
                        "136"    :     0x600E  ,
                        "137"    :     0x6004  ,
                        "138"    :     0x60A0  ,
                        "1381"   :     0x60A1  ,
                        "1382"   :     0x60A2  ,
                        "1383"   :     0x60A3  ,
                        "1384"   :     0x60A4  ,
                        "1385"   :     0x60B0  ,
                        "139"    :     0x6005  ,


                        "140"    :     0x5000   ,         #  Protest
                        "145"    :     0x50A0   ,

                        "150"    :     0x8000   ,         #  Exhibit Force Posture
                        "151"    :     0x8001   ,
                        "152"    :     0x8002   ,
                        "153"    :     0x8003   ,
                        "154"    :     0x8004   ,

                        "160"    :     0x0100   ,         #  Reduce Relations
                        "161"    :     0x0180   ,
                        "162"    :     0x0140   ,
                        "1621"   :     0x0145   ,
                        "1622"   :     0x0146   ,
                        "1623"   :     0x0147   ,
                        "163"    :     0x000B   ,
                        "164"    :     0x0110   ,
                        "165"    :     0x0130   ,
                        "166"    :     0x0150   ,
                        "1661"   :     0x0159   ,
                        "1662"   :     0x015A   ,
                        "1663"   :     0x015E   ,

                        "170"    :     0x9000    ,         #  Coerce
                        "171"    :     0x9010    ,
                        "1711"   :     0x9011    ,
                        "1712"   :     0x9012    ,
                        "172"    :     0x900B    ,
                        "1721"   :     0x9003    ,
                        "1722"   :     0x9001    ,
                        "1723"   :     0x9004    ,
                        "1724"   :     0x9006    ,
                        "173"    :     0x9020    ,
                        "174"    :     0x9030    ,
                        "175"    :     0x9040    ,

                        "180"    :     0x0090    ,         #  Assault
                        "181"    :     0x0091    ,
                        "182"    :     0x0092    ,
                        "1821"   :     0x0093    ,
                        "1822"   :     0x0094    ,
                        "1823"   :     0x0095    ,
                        "1824"   :     0x0096    ,
                        "183"    :     0x0097    ,
                        "1831"   :     0x0098    ,
                        "1832"   :     0x0099    ,
                        "1833"   :     0x009A    ,
                        "1834"   :     0x009B    ,
                        "184"    :     0x009C    ,
                        "185"    :     0x009D    ,
                        "186"    :     0x009E    ,


                        "190"    :     0x00A0    ,         #  Fight
                        "191"    :     0x00A1    ,
                        "192"    :     0x00A2    ,
                        "193"    :     0x00A3    ,
                        "194"    :     0x00A4    ,
                        "195"    :     0x00A5    ,
                        "1951"   :     0x00A6    ,
                        "1952"   :     0x00A7    ,
                        "196"    :     0x00A8    ,

                        "200"    :     0x00B0    ,         #  Use Unconventional Mass Violence
                        "---"    : 0              }

    if forward:
        passive = False
        active = code.split(":")
        passive = active[1] if len(active) > 1 else "---"
        active = active[0] if active[0] else "---"

        if active in cat:
            active = cat[active]
        else:
            active = cat[active[:2]+"0"]
        if passive in cat:
            passive = cat[passive]
        else:
            passive = cat[passive[:2]+"0"]

        return active, passive



    else:
        reverse = dict(map(lambda a : (a[1],a[0]) , cat.items())  + # Other weird quirks
                [   (0x30a0,"138"),   # Want to attack

                ])
        if code and code in reverse:
            return reverse[code]

        return 0 # hex(code)
