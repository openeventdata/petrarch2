##	PETRglobals.py [module]
##
# Global variable initializations for the PETRARCH event coder
##
# CODE REPOSITORY: https://github.com/eventdata/PETRARCH
##
# SYSTEM REQUIREMENTS This program has been successfully run under Mac OS 10.6;
# it is standard Python 2.5 so it should also run in Unix or Windows.
##
# PROVENANCE:
# Programmer: Philip A. Schrodt
# Parus Analytical Systems
# State College, PA, 16801 U.S.A.
# http://eventdata.parusanalytics.com
##
# Copyright (c) 2014	Philip A. Schrodt
##
# This project was funded in part by National Science Foundation grant SES-1259190
##
# This code is covered under the MIT license as asserted in the file PETR.coder.py
##
# Report bugs to: schrodt735@gmail.com
##
# REVISION HISTORY:
# 22-Nov-13:	Initial version -- ptab.verbsonly.py
# 28-Apr-14:	Latest version
# ------------------------------------------------------------------------

# Global variables are listed below: additional details on their structure can
# be found in various function definitions. The various options are described
# in more detail in the config.ini file.

VerbDict = {}  # verb dictionary
ActorDict = {}  # actor dictionary
ActorCodes = []  # actor code list
AgentDict = {}  # agent dictionary
DiscardList = []  # discard list
IssueList = []
IssueCodes = []

ConfigFileName = "PETR_config.ini"
VerbFileName = ""  # verb dictionary
ActorFileList = []  # actor dictionary
AgentFileName = ""  # agent dictionary
DiscardFilename = ""  # discard list
TextFileList = []  # current text or validation file
EventFileName = ""  # event output file
IssueFileName = ""  # issues list

# element followed by attribute and content pairs for XML line
AttributeList = []

# CODING OPTIONS
# Defaults are more or less equivalent to TABARI
NewActorLength = 0  # Maximum length for new actors extracted from noun phrases
RequireDyad = True  # Events require a non-null source and target
StoponError = False  # Raise stop exception on errors rather than recovering

RunTimeString = ''  # used in error and debugging files -- just set it once

# INTERFACE OPTIONS: these can be changed in config.ini
# The default -- all false -- is equivalent to an A)utocode in TABARI
CodeBySentence = False
PauseBySentence = False
PauseByStory = False

# COMMA OPTION : These adjust the length (in words) of comma-delimited clauses
# that are eliminated from the parse. To deactivate, set the max to zero.
#         Defaults, based on TABARI, are in ()
#         comma_min :  internal clause minimum length [2]
#         comma_max :  internal clause maximum length [8]
#         comma_bmin : initial ("begin") clause minimum length [0]
#         comma_bmax : initial clause maximum length [0 : deactivated by default]
#         comma_emin : terminal ("end") clause minimum length [2]
#         comma_emax : terminal clause maximum length [8]
CommaMin = 2
CommaMax = 8
CommaBMin = 0
CommaBMax = 0
CommaEMin = 2
CommaEMax = 8

stanfordnlp = ''
