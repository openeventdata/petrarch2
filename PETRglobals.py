##	PETRglobals.py [module]
##
##  Global variable initializations for the PETRARCH event coder 
##
##  CODE REPOSITORY: https://github.com/eventdata/PETRARCH
##
##	SYSTEM REQUIREMENTS
##	This program has been successfully run under Mac OS 10.6; it is standard Python 2.5
##	so it should also run in Unix or Windows. 
##
##	PROVENANCE:
##	Programmer: Philip A. Schrodt
##				Parus Analytical Systems
##				State College, PA, 16801 U.S.A.
##				http://eventdata.parusanalytics.com
##
##	Copyright (c) 2013	Philip A. Schrodt.	All rights reserved.
##
## This project was funded in part by National Science Foundation grant 
## SES-1259190
##
##	Redistribution and use in source and binary forms, with or without modification,
##	are permitted under the terms of the GNU General Public License:
##	http://www.opensource.org/licenses/gpl-license.html
##
##	Report bugs to: schrodt735@gmail.com
##
##	REVISION HISTORY:
##	22-Nov-13:	Initial version -- ptab.verbsonly.py
##	----------------------------------------------------------------------------------

# Global variables are listed below: additional details on their structure can be
# found in various function definitions

VerbDict = {}  # verb dictionary
ActorDict = {}  # actor dictionary
ActorCodes = []  # actor code list
AgentDict = {}  # agent dictionary
DiscardList = []  # discard list
IssueList = []
IssueCodes = []

ConfigFileName = "PETR_config.ini"
VerbFileName = ""  # verb dictionary
ActorFileList = [] # actor dictionary
AgentFileName = "" # agent dictionary
DiscardFilename = "" # discard list
TextFileList = []  # current text or validation file
EventFileName = "" # event output file
IssueFileName = "" # issues list

RunTimeString = '' # used in error and debugging files -- just set it once
CodeBySentence = False
PauseBySentence = False
PauseByStory = False



