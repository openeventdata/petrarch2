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
# Summer-14:	Initial version
# ------------------------------------------------------------------------


from __future__ import print_function
from __future__ import unicode_literals

import os
import logging
import corenlp
import dateutil.parser
import PETRglobals
from collections import defaultdict, Counter

import numpy



def stanford_parse(event_dict):
    logger = logging.getLogger('petr_log')
    # What is dead can never die...
    print("\nSetting up StanfordNLP. The program isn't dead. Promise.")
    logger.info('Setting up StanfordNLP')
    core = corenlp.StanfordCoreNLP(PETRglobals.stanfordnlp,
                                   properties=_get_data('data/config/',
                                                        'petrarch.properties'),
                                   memory='2g')
    total = len(list(event_dict.keys()))
    print(
        "Stanford setup complete. Starting parse of {} stories...".format(total))
    logger.info(
        'Stanford setup complete. Starting parse of {} stories.'.format(total))
    for i, key in enumerate(event_dict.keys()):
        if (i / float(total)) * 100 in [10.0, 25.0, 50, 75.0]:
            print('Parse is {}% complete...'.format((i / float(total)) * 100))
        for sent in event_dict[key]['sents']:
            logger.info('StanfordNLP parsing {}_{}...'.format(key, sent))
            sent_dict = event_dict[key]['sents'][sent]

            if len(sent_dict['content']) > 512 or len(
                    sent_dict['content']) < 64:
                logger.warning(
                    '\tText length wrong. Either too long or too short.')
                pass
            else:
                try:
                    stanford_result = core.raw_parse(sent_dict['content'])
                    s_parsetree = stanford_result['sentences'][0]['parsetree']
                    if 'coref' in stanford_result:
                        sent_dict['coref'] = stanford_result['coref']

                    # TODO: To go backwards you'd do str.replace(' ) ', ')')
                    sent_dict['parsed'] = _format_parsed_str(s_parsetree)
                except Exception as e:
                    print('Something went wrong. ¯\_(ツ)_/¯. See log file.')
                    logger.warning(
                        'Error on {}_{}. ¯\_(ツ)_/¯. {}'.format(key, sent, e))
    print('Done with StanfordNLP parse...\n\n')
    logger.info('Done with StanfordNLP parse.')

    return event_dict



def parse_to_text(parse):
    x = filter(lambda a : not a.startswith("("), parse.replace(")","").split())
    r = "" + x[0]
    for item in x[1:]:
        r += " " + item
    return r

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
            events = story_dict['sents'][sent]['events']
            for event in events:
                # do not print unresolved agents
                try:
                    if event[0][0] != '-' and event[1][0] != '-':
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

                        # Will keep track of this info, but not necessarily write it
                        # out
                        filtered[event_tuple]['ids'] = []
                        filtered[event_tuple]['ids'].append(sent_id)
                except IndexError:
                    pass
        else:
            pass

    return filtered


def _format_parsed_str(parsed_str):
    if parsed_str.startswith("(ROOT") and parsed_str.endswith(")"):
        parsed_str = parsed_str[5:-1].strip()
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

    #print(selfcode,to_add)
    if selfcode < 0:
        return -to_add
    if to_add >= selfcode:
        return to_add
    if selfcode >= 0x1000 and to_add >= 0x1000:
        return to_add  # If both verbs are high-level, take the lower nested one. I think this is what we want?
    return selfcode + to_add

    """
    if hex(selfcode).startswith('0x5'):
        return selfcode
    
    if to_add/256  > 0 and 7 <= selfcode/256 and selfcode/256 <= 9: # Remap "intend to attack" as threaten
        category = to_add/256
        if category == 3:
            return 0x600 + selfcode
        elif category == 6:
            return  selfcode + to_add

        elif category == 5:
            subcat = (to_add /16) % 16
            if subcat == 3:
                return 0x536
            if subcat == 1:
                return 0x515


    if to_add/256 > 0 and selfcode/256 > 0:
        return selfcode

    return selfcode + to_add
    """



def code_to_string(events):
    retstr= ""
    try:
        def ev_to_string(ev):
            local = ""
            #print(ev)
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
    except:
        return "ERROR "+str(events)




def convert_code(code):

    if ':' in code:
        code = code[:3]
        #print("\t\tWHADDUP",code)
    """
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
 
    
    
    
                      # Old      :     New           #  Top-level codes in the new system
                      
    cat = {             "010"    :     [1,0,0,0] ,         #  Make Public Statement
                        "011"    :     [1,0,0,0] ,
                        "012"    :     [1,0,0,0] ,
                        "013"    :     [1,0,0,0]  ,
                        "014"    :     [1,0,0,0]  ,
                        "015"    :     [1,0,0,0]  ,
                        "016"    :     [1,0,0,0]  ,
                        "017"    :     [1,0,0,0]  ,
                        "018"    :     [1,0,0,0]  ,
                        "019"    :     [1,0,0,0]  ,

    
                        "020"    :     [2,0,0,0]  ,         #  Appeal
                        "021"    :     [2,0,7,0]  ,
                        "0211"   :     [2,0,7,5]  ,
                        "0212"   :     [2,0,7,6]  ,
                        "0213"   :     [2,0,7,8]  ,
                        "0214"   :     [2,0,7,10] ,
                        "022"    :     [2,0,8,0]  ,
                        "023"    :     [2,0,4,0]  ,
                        "0231"   :     [2,0,4,5]  ,
                        "0232"   :     [2,0,4,6]  ,
                        "0233"   :     [2,0,4,7]  ,
                        "0234"   :     [2,0,4,9]  ,
                        "024"    :     [2,0,6,0]  ,
                        "0241"   :     [2,0,6,1]  ,
                        "0242"   :     [2,0,6,2]  ,
                        "0243"   :     [2,0,6,3]  ,
                        "0244"   :     [2,0,6,4]  ,
                        "025"    :     [2,2,0,0]  ,
                        "0251"   :     [2,2,0,11]  ,
                        "0252"   :     [2,2,0,12]  ,
                        "0253"   :     [2,2,0,13]  ,
                        "0254"   :     [2,2,0,5]  ,
                        "0255"   :     [2,2,0,14]  ,
                        "0256"   :     [2,2,0,15]  ,
                        "026"    :     [2,0,1,0]  ,
                        "027"    :     [2,0,2,0]  ,
                        "028"    :     [2,0,3,0]  ,
                        
                        
                        "030"    :     [3,0,0,0]  ,         #  Intend
                        "031"    :     [3,0,7,0]  ,
                        "0311"   :     [3,0,7,5]  ,
                        "0312"   :     [3,0,7,6]  ,
                        "0313"   :     [3,0,7,8]  ,
                        "0314"   :     [3,0,7,10] ,
                        "032"    :     [3,0,8,0]  ,
                        "033"    :     [3,0,4,0]  ,
                        "0331"   :     [3,0,4,5]  ,
                        "0332"   :     [3,0,4,6]  ,
                        "0333"   :     [3,0,4,7]  ,
                        "0334"   :     [3,0,4,9]  ,
                        "034"    :     [3,0,6,0]  ,
                        "0341"   :     [3,0,6,1]  ,
                        "0342"   :     [3,0,6,2]  ,
                        "0343"   :     [3,0,6,3]  ,
                        "0344"   :     [3,0,6,4]  ,
                        "035"    :     [3,2,0,0]  ,
                        "0351"   :     [3,2,0,11]  ,
                        "0352"   :     [3,2,0,12]  ,
                        "0353"   :     [3,2,0,13]  ,
                        "0354"   :     [3,2,0,5]  ,
                        "0355"   :     [3,2,0,14]  ,
                        "0356"   :     [3,2,0,15]  ,
                        "036"    :     [3,0,1,0]  ,
                        "037"    :     [3,0,2,0]  ,
                        "038"    :     [3,2,3,0]  ,
                        "039"    :     [3,0,3,0]  ,
                        
                        "040"    :     [11,0,0,0]   ,         #  Consult
                        "041"    :     [11,0,0,0]   ,
                        "042"    :     [11,0,0,0]  ,
                        "043"    :     [11,0,0,0]  ,
                        "044"    :     [11,0,1,0] ,
                        "045"    :     [11,0,3,0]   ,
                        "046"    :     [11,0,1,0] ,
                        
                        
                        "050"    :     [0,0,8,0]   ,        # Diplomatic Coop
                        "051"    :     [0,0,8,0]   ,
                        "052"    :     [0,0,8,0]  ,
                        "053"    :     [0,0,8,0]   ,
                        "054"    :     [0,0,8,0]   ,
                        "055"    :     [0,0,8,0]   ,
                        "056"    :     [0,0,8,0]   ,
                        "057"    :     [0,0,8,0]   ,
                        
                        "060"    :     [0,0,7,0]   ,        # Material Coop
                        "061"    :     [0,0,7,0]   ,
                        "062"    :     [0,0,7,0]   ,
                        "063"    :     [0,0,7,0]   ,
                        "064"    :     [0,0,7,0]   ,

                        "070"    :     [0,0,4,0]   ,        # Provide Aid
                        "071"    :     [0,0,4,0]   ,
                        "072"    :     [0,0,4,0]   ,
                        "073"    :     [0,0,4,0]   ,
                        "074"    :     [0,0,4,0]  ,
                        "075"    :     [0,0,4,0]   ,
                    
                        "080"    :     [0,2,0,0]   ,         #  Yield
                        "081"    :     [0,2,0,0]    ,
                        "0811"   :     [0,2,0,0]    ,
                        "0812"   :     [0,2,0,0]    ,
                        "0813"   :     [0,2,0,0]    ,
                        "0814"   :     [0,2,0,0]    ,
                        "082"    :     [0,2,0,0]    ,
                        "083"    :     [0,2,0,0]   ,
                        "0831"   :     [0,2,0,0]    ,
                        "0832"   :     [0,2,0,0]    ,
                        "0833"   :     [0,2,0,0]   ,
                        "0834"   :     [0,2,0,0]    ,
                        "084"    :     [0,2,0,0]    ,
                        "0841"   :     [0,2,0,0]    ,
                        "0842"   :     [0,2,0,0]    ,
                        "085"    :     [0,2,0,0]    ,
                        "086"    :     [0,2,0,0]    ,
                        "0861"   :     [0,2,0,0]    ,
                        "0862"   :     [0,2,0,0]    ,
                        "0863"   :     [0,2,0,0]    ,
                        "087"    :     [0,2,0,0]    ,
                        "0871"   :     [0,2,0,0]    ,
                        "082"    :     [0,2,0,0]    ,
                        "083"    :     [0,2,0,0]    ,
                        "084"    :     [0,2,0,0]    ,
                        
                        
                        "090"    :     [0,10,0,0]    ,         #  Investigate
                        "091"    :     [0,10,0,0]   ,
                        "092"    :     [0,10,0,0]   ,
                        "093"    :     [0,10,0,0]  ,
                        "094"    :     [0,10,0,0]  ,
                        
                        "100"    :     [4,0,0,0]  ,         #  Demand
                        "101"    :     [4,0,7,0]  ,
                        "1011"   :     [4,0,7,5]  ,
                        "1012"   :     [4,0,7,6]  ,
                        "1013"   :     [4,0,7,8]  ,
                        "1014"   :     [4,0,7,10] ,
                        "102"    :     [4,0,8,0]  ,
                        "103"    :     [4,0,4,0]  ,
                        "1031"   :     [4,0,4,5]  ,
                        "1032"   :     [4,0,4,6]  ,
                        "1033"   :     [4,0,4,7]  ,
                        "1034"   :     [4,0,4,9]  ,
                        "104"    :     [4,0,6,0]  ,
                        "1041"   :     [4,0,6,1]  ,
                        "1042"   :     [4,0,6,2]  ,
                        "1043"   :     [4,0,6,3]  ,
                        "1044"   :     [4,0,6,4]  ,
                        "105"    :     [4,2,0,0]  ,
                        "1051"   :     [4,2,0,11]  ,
                        "1052"   :     [4,2,0,12]  ,
                        "1053"   :     [4,2,0,13]  ,
                        "1054"   :     [4,2,0,5]  ,
                        "1055"   :     [4,2,0,14]  ,
                        "1056"   :     [4,2,0,15]  ,
                        "106"    :     [4,0,1,0]  ,
                        "107"    :     [4,0,2,0]  ,
                        "108"    :     [4,0,3,0]  ,

                        
                        "110"    :     [7,0,0,0]   ,         #  Disapprove
                        "111"    :     [7,0,0,0]  ,
                        "112"    :     [7,0,0,0]   ,
                        "1121"   :     [7,0,0,0]   ,
                        "1122"   :     [7,0,0,0]  ,
                        "1123"   :     [7,0,0,0]   ,
                        "1124"   :     [7,0,0,0]   ,
                        "1125"   :     [7,0,0,0]   ,
                        "113"    :     [7,0,0,0]   ,
                        "114"    :     [7,0,0,0]   ,
                        "115"    :     [7,0,0,0]   ,
                        "116"    :     [7,0,0,0]  ,
                        
                        
                        "12"     :   -1 ,
              #          "120"    :     0xA00  ,         #  Reject
              #          "121"    :     0xA70  ,
              #          "1211"   :     0xA75  ,
              #          "1212"   :     0xA76  ,
              #          "122"    :     0xB40  ,      ### THESE ALSO HAVE DEMAND COUNTERPARTS
              #          "1221"   :     0xB45  ,
              #          "1222"   :     0xB46  ,
              #          "1223"   :     0xB47  ,
              #          "1224"   :     0xB49  ,
              #          "123"    :     0xB60  ,
              #          "1231"   :     0xB61  ,
              #          "1232"   :     0xB62  ,
              #          "1233"   :     0xB63  ,
              #          "1234"   :     0xB64  ,
              #          "124"    :     0xA90  ,
              #          "1241"   :     0xA9B  ,
              #          "1242"   :     0xA9C  ,
              #          "1243"   :     0xA9D  ,
              #          "1244"   :     0xA95  ,
              #          "1245"   :     0xA9E  ,
              #          "1246"   :     0xA9F  ,
              #          "125"    :     0xA10  ,
              #         "126"    :     0xA30  ,
              #         "127"    :     0xA20  ,
              #          "128"    :     0xA01  ,
              #          "129"    :     0xA02  ,
              
                        "130"    :     [6,0,0,0]  ,         #  Threaten
                        "131"    :     [6,0,0,0] ,
                        "1311"   :     [6,0,0,0]  ,
                        "1312"   :     [6,0,0,0]  ,
                        "1313"   :     [6,0,0,0]  ,
                        "132"    :     [6,0,0,0]  ,
                        "1321"   :     [6,0,0,0]  ,
                        "1322"   :     [6,0,0,0]  ,
                        "1323"   :     [6,0,0,0]  ,
                        "1324"   :     [6,0,0,0]  ,
                        "133"    :     [6,0,0,0]  ,
                        "134"    :     [6,0,0,0]  ,
                        "135"    :     [6,0,0,0]  ,
                        "136"    :     [6,0,0,0]  ,
                        "137"    :     [6,0,0,0]  ,
                        "138"    :     [6,0,0,0]  ,
                        "1381"   :     [6,0,0,0]  ,
                        "1382"   :     [6,0,0,0]  ,
                        "1383"   :     [6,0,0,0]  ,
                        "1384"   :     [6,0,0,0]  ,
                        "1385"   :     [6,0,0,0]  ,
                        "139"    :     [6,0,0,0]  ,
                        
                        
                        "14"     :     [5,0,0,0]   ,         #  Protest
                        
                        "15"     :     [8,0,0,0]   ,         #  Exhibit Force Posture
                        
                        "160"    :     [0,1,0,0]   ,         #  Reduce Relations
                        "161"    :     [0,1,0,0]   ,
                        "162"    :     [0,1,0,0]   ,
                        "1621"   :     [0,1,0,0]   ,
                        "1622"   :     [0,1,0,0]   ,
                        "1623"   :     [0,1,0,0]   ,
                        "163"    :     [0,1,0,0]   ,
                        "164"    :     [0,1,0,0]   ,
                        "165"    :     [0,1,0,0]   ,
                        "166"    :     [0,1,0,0]   ,
                        "1661"   :     [0,1,0,0]   ,
                        "1662"   :     [0,1,0,0]   ,
                        "1663"   :     [0,1,0,0]   ,
                        
                        "17"    :     [9,0,0,0]    ,         #  Coerce
                        "18"    :     [0,0,9,0]    ,         #  Assault
                        "19"    :     [0,0,10,0]    ,         #  Fight
                        "20"    :     [0,0,11,0]    ,   }      #  Use Unconventional Mass Violence
    
    """
    cat = {             "010"    :     0x1000 ,         #  Make Public Statement
                        "011"    :     0x1000 ,
                        "012"    :     0x1000 ,
                        "013"    :     0x1000  ,
                        "014"    :     0x1000  ,
                        "015"    :     0x1000  ,
                        "016"    :     0x1000  ,
                        "017"    :     0x1000  ,
                        "018"    :     0x1000  ,
                        "019"    :     0x1000  ,

    
                        "020"    :     0x2000  ,         #  Appeal
                        "021"    :     0x2070  ,
                        "0211"   :     0x2075  ,
                        "0212"   :     0x2076  ,
                        "0213"   :     0x2078  ,
                        "0214"   :     0x207A ,
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
                        
                        
                        "030"    :     0x3000   ,         #  Intend
                        "031"    :     0x3070  ,
                        "0311"   :     0x3075  ,
                        "0312"   :     0x3076  ,
                        "0313"   :     0x3078  ,
                        "0314"   :     0x307A ,
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
                        "041"    :     0xB000  ,
                        "042"    :     0xB000  ,
                        "043"    :     0xB000  ,
                        "044"    :     0xB010  ,
                        "045"    :     0xB030  ,
                        "046"    :     0xB010  ,
                        
                        
                        "050"    :     0x0080  ,        # Diplomatic Coop
                        "051"    :     0x0080   ,
                        "052"    :     0x0080  ,
                        "053"    :     0x0080   ,
                        "054"    :     0x0080   ,
                        "055"    :     0x0080   ,
                        "056"    :     0x0080   ,
                        "057"    :     0x0080   ,
                        
                        "060"    :     0x0070   ,        # Material Coop
                        "061"    :     0x0070   ,
                        "062"    :     0x0070   ,
                        "063"    :     0x0070   ,
                        "064"    :     0x0070   ,

                        "070"    :     0x0040   ,        # Provide Aid
                        "071"    :     0x0040   ,
                        "072"    :     0x0040   ,
                        "073"    :     0x0040   ,
                        "074"    :     0x0040   ,
                        "075"    :     0x0040   ,
                    
                        "080"    :     0x0200   ,         #  Yield
                        "081"    :     0x0200    ,
                        "0811"   :     0x0200   ,
                        "0812"   :     0x0200    ,
                        "0813"   :     0x0200    ,
                        "0814"   :     0x0200    ,
                        "082"    :     0x0200    ,
                        "083"    :     0x0200   ,
                        "0831"   :     0x0200   ,
                        "0832"   :     0x0200    ,
                        "0833"   :     0x0200   ,
                        "0834"   :     0x0200    ,
                        "084"    :     0x0200   ,
                        "0841"   :     0x0200   ,
                        "0842"   :     0x0200   ,
                        "085"    :     0x0200    ,
                        "086"    :     0x0200    ,
                        "0861"   :     0x0200    ,
                        "0862"   :     0x0200   ,
                        "0863"   :     0x0200   ,
                        "087"    :     0x0200   ,
                        "0871"   :     0x0200   ,
                        "082"    :     0x0200 ,
                        "083"    :     0x0200 ,
                        "084"    :     0x0200 ,
                        "08"     :     0x0200 ,
                        
                        "090"    :     0xA000  ,         #  Investigate
                        "091"    :     0xA000  ,
                        "092"    :     0xA000  ,
                        "093"    :     0xA000  ,
                        "094"    :     0xA000  ,
                        
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

                        
                        "110"    :     0x7000   ,         #  Disapprove
                        "111"    :     0x7000  ,
                        "112"    :     0x7000   ,
                        "1121"   :     0x7000   ,
                        "1122"   :     0x7000  ,
                        "1123"   :     0x7000   ,
                        "1124"   :     0x7000   ,
                        "1125"   :     0x7000   ,
                        "113"    :     0x7000   ,
                        "114"    :     0x7000   ,
                        "115"    :     0x7000   ,
                        "116"    :     0x7000  ,
                        
                        
                        "12"     :   -1 ,
              #          "120"    :     0xA00  ,         #  Reject
              #          "121"    :     0xA70  ,
              #          "1211"   :     0xA75  ,
              #          "1212"   :     0xA76  ,
              #          "122"    :     0xB40  ,      ### THESE ALSO HAVE DEMAND COUNTERPARTS
              #          "1221"   :     0xB45  ,
              #          "1222"   :     0xB46  ,
              #          "1223"   :     0xB47  ,
              #          "1224"   :     0xB49  ,
              #          "123"    :     0xB60  ,
              #          "1231"   :     0xB61  ,
              #          "1232"   :     0xB62  ,
              #          "1233"   :     0xB63  ,
              #          "1234"   :     0xB64  ,
              #          "124"    :     0xA90  ,
              #          "1241"   :     0xA9B  ,
              #          "1242"   :     0xA9C  ,
              #          "1243"   :     0xA9D  ,
              #          "1244"   :     0xA95  ,
              #          "1245"   :     0xA9E  ,
              #          "1246"   :     0xA9F  ,
              #          "125"    :     0xA10  ,
              #         "126"    :     0xA30  ,
              #         "127"    :     0xA20  ,
              #          "128"    :     0xA01  ,
              #          "129"    :     0xA02  ,
              
                        "130"    :     0x6000  ,         #  Threaten
                        "131"    :     0x6000 ,
                        "1311"   :     0x6000  ,
                        "1312"   :     0x6000  ,
                        "1313"   :     0x6000  ,
                        "132"    :     0x6000  ,
                        "1321"   :     0x6000  ,
                        "1322"   :     0x6000  ,
                        "1323"   :     0x6000  ,
                        "1324"   :     0x6000  ,
                        "133"    :     0x6000  ,
                        "134"    :     0x6000  ,
                        "135"    :     0x6000  ,
                        "136"    :     0x6000  ,
                        "137"    :     0x6000  ,
                        "138"    :     0x6000  ,
                        "1381"   :     0x6000  ,
                        "1382"   :     0x6000  ,
                        "1383"   :     0x6000  ,
                        "1384"   :     0x6000  ,
                        "1385"   :     0x6000  ,
                        "139"    :     0x6000  ,
                        
                        
                        "14"     :     0x5000   ,         #  Protest
                        
                        "15"     :     0x8000   ,         #  Exhibit Force Posture
                        
                        "160"    :     0x0100   ,         #  Reduce Relations
                        "161"    :     0x0100   ,
                        "162"    :     0x0100  ,
                        "1621"   :     0x0100,
                        "1622"   :     0x0100  ,
                        "1623"   :     0x0100  ,
                        "163"    :     0x0100   ,
                        "164"    :     0x0100   ,
                        "165"    :     0x0100   ,
                        "166"    :     0x0100   ,
                        "1661"   :     0x0100   ,
                        "1662"   :     0x0100   ,
                        "1663"   :     0x0100   ,
                        
                        "17"    :     0x9000    ,         #  Coerce
                        "18"    :     0x0090    ,         #  Assault
                        "19"    :     0x00A0    ,         #  Fight
                        "20"    :     0x00B0    ,         #  Use Unconventional Mass Violence
                        "---"   : 0              }

    if code in cat:
        if not code == -1:
            return cat[code]
        return -1
    return cat[code[:2]]

