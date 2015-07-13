##	PETRglobals.py [module]
##
# Global variable initializations for the PETRARCH event coder
#
# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.10; it is standard Python 2.7
# so it should also run in Unix or Windows.
#
# INITIAL PROVENANCE:
# Programmer: Philip A. Schrodt
#			  Parus Analytics
#			  Charlottesville, VA, 22901 U.S.A.
#			  http://eventdata.parusanalytics.com
#
# GitHub repository: https://github.com/openeventdata/petrarch
#
# Copyright (c) 2014	Philip A. Schrodt.	All rights reserved.
#
# This project is part of the Open Event Data Alliance tool set; earlier developments
# were funded in part by National Science Foundation grant SES-1259190
#
# This code is covered under the MIT license
#
# REVISION HISTORY:
# 22-Nov-13:	Initial version -- ptab.verbsonly.py
# 28-Apr-14:	Latest version
# 20-Nov-14:	WriteActorRoot/Text added
# ------------------------------------------------------------------------

# Global variables are listed below: additional details on their structure can
# be found in various function definitions. The various options are described
# in more detail in the config.ini file.

VerbDict = {}  # verb dictionary
ActorDict = {}  # actor dictionary
ActorCodes = []  # actor code list
AgentDict = {}  # agent dictionary
DiscardList = {}  # discard list
IssueList = []
IssueCodes = []

ConfigFileName = "PETR_config.ini"
VerbFileName = ""  # verb dictionary
ActorFileList = []  # actor dictionary
AgentFileName = ""  # agent dictionary
DiscardFileName = ""  # discard list
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

# OUTPUT OPTIONS
WriteActorRoot = False  # Include actor root in event record
WriteActorText = False  # Include actor text in event record

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

# TEMPORARY VARIABLES
# <14.11.20> Temporary in the sense that these won't be needed when we eventually
# refactor so that codes are some sort of structure other than a string
CodePrimer = '=#='   # separates actor code from root and text strings
RootPrimer = CodePrimer + ':'  # start of root string
TextPrimer = CodePrimer + '+'  # start of text string
