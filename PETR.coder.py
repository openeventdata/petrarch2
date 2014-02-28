"""
PETR.coder.py

Development environment for the PETRARCH event coder. 

STATUS OF THE PROGRAM 28-FEBRUARY-2014

I've decided to commit this to GitHub since it is basically functional and there were 
concerns that the project had died. Actually, it's merely resting, pining for the fjords.

No, really, there are about 1700 lines of more or less debugged code here (64 functions,
and about as many lines of comments and documentation)  and these are sufficient for a 
very basic coder. My guess is that it needs another 5 to 8 days of work to get all of the 
functionality of TABARI, and some of the basic structures may change -- in particular, 
it currently does not accommodate synonym sets -- but for the most part it seems solid 
(e.g. I was able to add the discard and issues facilities with a minimum of trouble). 

But only "for the most part": there are still about a half dozen bugs in the main coding 
routine. These are trapped with exceptions: the program coded 60,000 AFP stories from 
the GigaWord corpus without crashing, so these seem to be the only lethal bugs. That 
said, because the TABARI pattern matching is not fully implemented, it is not getting 
nearly as many events as TABARI would on the same data: in the current state, you can think 
of this as an extremely conservative coder. 

Documentation is really thorough in some places, less so in others. This will all 
eventually be incorporated into a manual similar to the TABARI manual.

I'm probably not going to be able to get back to this for about a month, but *hope* to get 
the rest of that work done in April-2014. Though I would welcome additional work, 
extensions, cleaning up my lousy Python, etc in the meantime. 

[What the heck is TABARI??: http://eventdata.parusanalytics.com/software.dir/tabari.html]
   
------------------------------------------------------------------------------------- 

TO RUN PROGRAM: 
   Coding run:  
     python PETR.coder.py <options>
	-c <filename>: Use the configuration file <filename> 
	-e <filename>: <filename> is the event output file
	-t <filename>: Code the single text file <filename> 
	
	Validation and unit-test files:
 			python PETR.coder.py -v PETR.Validate.records.txt [development: not all work]
 			python PETR.coder.py -v PETR.UnitTest.records.txt [all should code correctly]

REQUIRED MODULES
   PETRglobals.py: global declarations
   PETRreader.pyc: dictionary input routines
   PETRwriter.pyc: output routines

INPUT FILES
	PETR_config.ini specifies the various files in a coding run 
	Validation files are set in the <Environment> block

OUTPUT FILES
	Event output is set using eventfile_name 
	Error file: hard coded to ErrorLog.PETR.txt or set using <Errorfile> tag (validation)
    Actor dictionary dump: ActorDict.content.txt [commented out]

PROGRAMMING NOTES

1. There is a fair amount of internal documentation in both multi-line comment blocks
   and individual comments, though as always this could be a little more systematic.

2. There are an assortment of general diagnostic print statements controlled by the
   Boolean switches in the DEBUGGING GLOBALS. In addition, a wide variety of function-
   specific print statements have been left in the code but commented out.    

CODE REPOSITORY: https://github.com/openeventdata/PETRARCH

SYSTEM REQUIREMENTS
This program has been successfully run under Mac OS 10.6.8, Ubuntu 12.2 and whatever  
version of Unix running on the Penn State HPC systems; it is standard Python 2.6.1 so it 
should conceivably also run in Windows. 

PROVENANCE:
Programmer: Philip A. Schrodt
			Parus Analytical Systems
			State College, PA, 16801 U.S.A.
			http://eventdata.parusanalytics.com

Copyright (c) 2014	Philip A. Schrodt.	All rights reserved.

This project was funded in part by National Science Foundation grant SES-1259190
(Directorate for Social, Behavioral and Economic Sciences; joint funding from the
Political Science and the Methods, Measurement and Statistics Programs.) Yes, *that* NSF
Political Science program.

Redistribution and use in source and binary forms, with or without modification,
are permitted under the terms of the GNU General Public License:
http://www.opensource.org/licenses/gpl-license.html

Report bugs to: schrodt735@gmail.com

REVISION HISTORY:
July-11: Initial version -- ptab.verbsonly.py
June-13: Revised to handle PETRARCH chunked format
July-13: Revised to handle Stanford NLP tree format
Nov-13:  Validation, PETRreader module
Dec-13:  Compound actors and agents
Feb-14:  do_coding, PETR_config.ini, discards, issues, runtime error trapping
         
----------------------------------------------------------------------------------

IMPLEMENTATION NOTES:

NAMING CONVENTIONS

GlobalVariables (those which may appear in 'global' statements) are named with the
CapitalizedWords style

localvariables are lowercase

functions are lower_case_with_underscores

-------------------------------------------------------------------------------------

VOCABULARY [mostly inherited from TABARI]

"upper" and "lower" matches 

These refer to the part of the pattern before (upper) and 
after ("lower") the verb designator ('*'). This convention arises from how a sentence
is usually printed, with the earlier words on the screen above the later words.

"connector"

This is the ' ' or '_' which follows a word: a '_' means that the next word must be
consecutive; a ' ' means that intermediate words can occur.

-------------------------------------------------------------------------------------

DIFFERENCES FROM TABARI

[which will be of little interest unless you are one of the fifty or so people in the
world who actually worked with TABARI, but it is possible that you've got an old TABARI
dictionary and some of this might be relevant.]

1. Requires a Penn TreeBank parsed version of the sentence as input and Stanford NLP
   coreferences

2. There is no stemming: if you need a stem, use a synset

3. Only named entities (NE) can match actors (though transformations of more complex
   phrases into are allowed)
   
4. Matching following the verb is restricted to the actual verb phrase(!!). Matching
   prior to the verb is probably more or less equivalent to what TABARI did
   
5. Input format is considerably more complex and contains embedded XML

-------------------------------------------------------------------------------------

NOTES FOR THE MANUAL 

1. There are an assortment of comments that contain the string '???' which indicate
   points that need to be clarified when re-writing the TABARI manual.

-------------------------------------------------------------------------------------

"""

import sys
import time

import PETRglobals  # global variables
import PETRreader # input routines
import PETRwriter # output routines

	
# ================================  PARSER/CODER GLOBALS  ================================ #	

ParseList = []   # linearized version of parse tree
ParseStart = 0   # first element to check (skips (ROOT, initial (S
ParseEnd = 0     # last element to check: skips final punctuation

UpperSeq = []  # text that can be matched prior to the verb; this is stored in reverse order
LowerSeq = []  # text that can be matched following the verb

SourceLoc = 0  # location of the source within the Upper/LowerSeq
TargetLoc = 0  # location of the target within the Upper/LowerSeq

SentenceID = ''   # ID line
EventCode = ''   # event code from the current verb
SourceCode = ''   # source code from the current verb
TargetCode = ''   # target code from the current verb

	
# ================================  VALIDATION GLOBALS  ================================ #	

DoValidation = False   # using a validation file
ValidOnly = False      # only evaluate cases where <Sentence valid="true">
CodedEvents = []  # validation mode : code triples that were produced; set in make_event_strings
ValidEvents = []  # validation mode : code triples that should be produced 
ValidInclude = []  # validation mode : list of categories to include 
ValidExclude = []  # validation mode : list of categories to exclude 
ValidPause = 0  # validation mode :pause conditions: 1: always; -1 never; 0 only on error [default] 

	
# ================================  UTILITY GLOBALS  ================================ #	

AttributeList = []  # element followed by attribute and content pairs for XML line

# ================================  DEBUGGING GLOBALS  ================================ #	

# (comment out the second line in the pair to activate. Like you couldn't figure that out.)

ShowParseList = True  # prints ParseList in evaluate_validation_record()
ShowParseList = False 

ShowCodingSeq = True  # prints upper and lower sequences ParseList in make_check_sequences()
ShowCodingSeq = False 

ShowPattMatch = True  # prints pattern match info in check_verbs()
ShowPattMatch = False 

ShowNEParsing = True  # prints search and intermediate strings in the (NE conversion
ShowNEParsing = False 

ShowMarkCompd = True  # prints search and intermediate strings in the (NE conversion
ShowMarkCompd = False 

# ================== EXCEPTIONS ================== #	

class DupError(Exception):  # template
	pass

class MissingAttr(Exception):  # could not find expected attribute field
	pass

class StopCoding(Exception):  # exit the coding
	pass

class SkipRecord(Exception):  # skip a validation record
	pass

class UnbalancedTree(Exception):  # unbalanced () in the parse tree
	pass
		
	
# ================== ERROR MESSAGE STRINGS ================== #	

ErrMsgExitValidation = "\nExiting: This information is required for running a validation file"
ErrMsgMissingDate = "<Sentence> missing required date; record was skipped"
ErrMsgUnbalancedTree = "Unbalanced <Parse> tree; record was skipped"				
	
def raise_parsing_error(call_location_string):
# <14.02.27: this is currently used as a generic escape from misbehaving functions, so it
# is not necessarily an actual unbalanced tree, just that we've hit something unexpected. 
	global SentenceID, NParseErrors, DoValidation
	errorstring = 'Parsing error in '+call_location_string
	PETRwriter.write_record_error(errorstring, SentenceID)
#	print errorstring
	if not DoValidation: NParseErrors += 1
	raise UnbalancedTree(errorstring)

	
# ========================== TAG EVAULATION FUNCTIONS ========================== #	
# <13.11.23> These can get moved to PETRreader once they stabilize
	
def find_tag(tagstr):
# reads fin until tagstr is found
# can inherit EOFError raised in PETRreader.read_FIN_line() 
	line = PETRreader.read_FIN_line() 
	while (tagstr not in line): 
		line = PETRreader.read_FIN_line() 

				
def extract_attributes(theline):
# puts list of attribute and content pairs in the global AttributeList. First item is
# the tag itself
# still to do: need error checking here
	""" Structure of attributes 
	At present, these always require a quoted field which follows an '=', though it 
	probably makes sense to make that optional and allow attributes without content 
	"""
	global AttributeList
#	print "PTR-1:", theline,		
	theline = theline.strip()
	if ' ' not in theline: # theline only contains a keyword
		AttributeList = theline[1:-2]
#		print "PTR-1.1:", AttributeList		
		return
	pline = theline[1:].partition(' ') # skip '<'
	AttributeList = [pline[0]]
	theline = pline[2]
	while ('=' in theline): # get the field and content pairs
		pline = theline.partition('=')
		AttributeList.append(pline[0].strip())
		theline = pline[2]
		pline = theline.partition('"')
		pline = pline[2].partition('"')
		AttributeList.append(pline[0].strip())
		theline = pline[2]
#	print "PTR-2:", AttributeList		

def check_attribute(targattr):
# Looks for targetattr in AttributeList; returns value if found, null string otherwise
# This is used if the attribute is optional (or if error checking is handled
# by the calling routine); if an error needs to be raised, use get_attribute() 
	global AttributeList
	if (targattr in AttributeList): return AttributeList[AttributeList.index(targattr)+1]
	else: return ""

def get_attribute(targattr):
# Similar to check_attribute except it raises a MissingAttr error when the attribute
# is missing.
	global AttributeList
	if (targattr in AttributeList): return AttributeList[AttributeList.index(targattr)+1]
	else:
		raise MissingAttr
		return ""
		 
def extract_Sentence_info(line):
# extracts fields for <Sentence record
# can raise SkipRecord if date is missing
	global SentenceDate, SentenceID, SentenceCat, SentenceLoc, SentenceValid
	extract_attributes(line)
	SentenceID = check_attribute('id')
	SentenceCat = check_attribute('category')
	SentenceLoc = check_attribute('place')
	if check_attribute('valid') == 'true': SentenceValid = True
	else: SentenceValid = False
	try: 
		SentenceDate = get_attribute('date')
	except MissingAttr:
		PETRwriter.write_FIN_error(ErrMsgMissingDate)
		raise SkipRecord


def extract_EventCoding_info(theline):
# extracts fields from <EventCoding record and appends to ValidEvents
# currently does not raise errors if the information is missing but instead sets the
# fields to null strings
	""" Structure of ValidEvents
	noevents: empty list
	otherwise list of triples of [sourcecode, targetcode, eventcode]
	"""
	global ValidEvents, AttributeList
	extract_attributes(theline)
	if ('noevents' in AttributeList[1]): 
		ValidEvents = []
		return
	else: 
#		print "EEC-1:",AttributeList
		ValidEvents.append([check_attribute('sourcecode'),check_attribute('targetcode'),check_attribute('eventcode')])

	
# ========================== VALIDATION FUNCTIONS ========================== #	
	
def evaluate_validation_record():
# read validation record, setting EventID and a list of correct coded events, code 
# using read_TreeBank, then check the results. Returns True if the lists of coded and
# expected events match or the event is skipped; false otherwise; also prints the mismatches
# raises EOFError exception if EOF hit.
# raises StopCoding if <Stop> found
# raises SkipRecord if <Skip> found or record is skipped due to In/Exclude category lists
	global SentenceDate, SentenceID, SentenceCat, SentenceText, SentenceValid
	global CodedEvents,ValidEvents
	global ValidInclude, ValidExclude, ValidPause, ValidOnly
	global ParseList
	global ShowParseList

	ValidEvents = []  # code triples that should be produced
	CodedEvents = []  # code triples that were produced; set in make_event_strings
	line = PETRreader.read_FIN_line() 
	while line: 
#		print line
		if ('<Sentence ' in line): 
			try : extract_Sentence_info(line)
			except MissingAttr: 
				print 'Skipping sentence: Missing date field in',line,
				return  # let SkipRecord be caught by calling routine
				
			if ValidOnly and not SentenceValid:
				raise SkipRecord
				return True
			
			if len(ValidInclude) > 0 and SentenceCat not in ValidInclude: 
				raise SkipRecord
				return True
			if len(ValidExclude) > 0 and SentenceCat in ValidExclude: 
				raise SkipRecord
				return True				
			
		if ('<EventCoding ' in line): 
			extract_EventCoding_info(line)
			print "EVR-2:",ValidEvents
			
		if ('<Text>' in line): 
			SentenceText = ''
			line = PETRreader.read_FIN_line()
			while '</Text>' not in line:
				SentenceText += line[:-1]
				if ' ' not in SentenceText[-1]: SentenceText += ' '
				line = PETRreader.read_FIN_line()
				
		if ('<Skip ' in line):  # handle skipping -- leave fin at end of tree
			print "EVR-1: <Skip"
			raise SkipRecord
			return True
			
		if ('<Stop>' in line): 
			raise StopCoding
			return True
			
		if '<Parse>' in line:
			try: 
				read_TreeBank()
				break
			except UnbalancedTree: # without the 'break', this will just skip processing the record and go to the next one
				PETRwriter.write_record_error(ErrMsgUnbalancedTree, SentenceID,SentenceCat) 
			
		line = PETRreader.read_FIN_line()

	print '\nSentence:',SentenceID,'[',SentenceCat,']'
	print SentenceText
#	print '**',ParseList
	assign_NEcodes()
#	print '**+',ParseList
	if ShowParseList: print 'EVR-Parselist::',ParseList

	check_verbs()
	
#	print 'EVR-2.1:',ValidEvents
#	print 'EVR-2.2:',CodedEvents

	if len(ValidEvents) > 0:
		print 'Expected Events:'
		for event in ValidEvents: print event
	else: print 'No events should be coded'
	
	if len(CodedEvents) > 0:
		print 'Coded Events:'
		for event in CodedEvents: print SentenceID + '\t' + event[0] + '\t' + event[1] + '\t' + event[2]
	else: print 'No events were coded'

	if (len(ValidEvents) == 0) and (len(CodedEvents) == 0): return True  # noevents option

	# compare the coded and expected events
	allokay = True
	ke = 0
	while ke < len(CodedEvents): # check that all coded events have matches
		kv = 0
		while kv < len(ValidEvents):
			if (len(ValidEvents[kv]) > 3): 
				kv += 1
				continue  # already matched
			else:
				if (CodedEvents[ke][0] == ValidEvents[kv][0]) and (CodedEvents[ke][1] == ValidEvents[kv][1]) and (CodedEvents[ke][2] == ValidEvents[kv][2]): 
					CodedEvents[ke].append('+')  # mark these as matched
					ValidEvents[kv].append('+')
					break
			kv += 1
		if (len(CodedEvents[ke]) == 3): 
			print "No match for the coded event:",CodedEvents[ke]
			allokay = False
		ke += 1
		
	for vevent in ValidEvents:  # check that all expected events were matched
		if (len(vevent) == 3): 
			print "No match for the expected event:",vevent
			allokay = False
	return allokay
	

def check_envirattr(line, stag, sattr):
# checks whether line contains sattr and exits with error if not found.
# this doesn't do anything with the attribute, just extracts the list and checks for it
	extract_attributes(line)
	try:  get_attribute(sattr)
	except MissingAttr:
		print "Missing '"+ sattr +"' field in "+ stag + " line",ErrMsgExitValidation
		sys.exit()

def open_validation_file():
	"""
1. Opens validation file TextFilename as FIN 
2. After "</Environment>" found, closes FIN, opens ErrorFile, sets various validation 
   options, then reads the dictionaries (exits if these are not set)
3. Can raise MissingXML
4. Can exit on EOFError, MissingAttr

 Validation File Format
	Validation files are used for debugging and unit testing, combining the contents
	of a project file and text file as well as providing information on the correct
	coding for each record. \footnote{This approach is used based on some decidedly 
	aggravating experiences during the TABARI development where the validation records 
	and the required .verbs and .actors files were not properly synchronized.}
	
	Required elements in the <Environment> block
		<Environment>
			<Verbfile name="<filename>">
			<Actorfile name="<filename>">  (there can only be one, unlike in the config 
			                                file, which allows a list)
			<Agentfile name="<filename>">
		</Environment>
	
	Options elements in the <Environment> block
		<Include categories="<space-delimited list of categories to include in test>">
			if 'valid' is included as a category, only records containing valid="true" 
			in <SENTENCE> will be evaluated. 
		<Exclude categories="<space-delimited list of categories to exclude in test>">
		[if a category is in both lists, the case is excluded. But please don't do this]
		<Pause value="<always, never>">
			Pause conditions: 
				always -- pause after every record
				never -- never pause (errors are still recorded in file)
				default -- pause only when EventCodes record doesn't correspond to the
						   generated events or if there is no EventCodes record 

	General record fields : all of these tags should occur on their own lines
	<Sentence>...</Sentence>:
		Delimits the record. The <Sentence...> tag can have the following fields:
		  date: date of the text in YYYYMMDD format. This is required; if it is not
				present the record will be skipped
		  id : identification string in any format [optional]
		  category: category in any format; this is used by the <Include> and <Exclude>
					options [optional]
		  place: code to be used for anonymous actors [optional]
	</Text>...</Text>: 
		delimits the source text. This is used only for the display. The tags should 
		occur on their own lines
	<Parse>...</Parse>
		Delimits the TreeBank parse tree text: this used only for the actual coding.
		The
	
	Required elements in each record: for validation, one or more of these should  
	occur prior to the TreeBank. If none are present, the record is coded and the
	program pauses unless <Pause value = "never'> has been used.
		<EventCodes sourcecode="<code>" targetcode="<code>" eventcode="<code>">
		<EventCodes noevents = "True"> : indicates the record generates no events
		  (presently, system just looks for the presence of a 'noevents' attribute)
		  
	Optional elements in record
		<Skip>: skip this record without coding
		<Stop>: stop coding and exit program
		
	Additional notes:
	1. The validation file currently does not use a discard file.
		
	=== EXAMPLE ===
	
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

	"""
	global ValidInclude, ValidExclude, ValidPause, ValidOnly
	global AttributeList

	PETRreader.open_FIN(PETRglobals.TextFileList[0],"validation")

	try: find_tag('<Environment')
	except EOFError:
		print "Missing <Environment> block in validation file\nExiting program"
		sys.exit()	

	gotErrorfile = False
	line = ""
	while "</Environment>" not in line:
		try: line = PETRreader.read_FIN_line() 
		except EOFError:
			print "Unexpected end of file, possibly due to missing </Environment> tag in validation file\nExiting program"
			sys.exit()	
		
		if ("<Verbfile " in line):	
			check_envirattr(line, '<Verbfile>','name')	
			PETRglobals.VerbFileName = get_attribute('name')
				
		if ("<Actorfile " in line):
			check_envirattr(line, '<Actorfile>','name')	
			PETRglobals.ActorFileList[0] = get_attribute('name')
			
		if ("<Agentfile " in line):
			check_envirattr(line, '<Agentfile>','name')	
			PETRglobals.AgentFileName = get_attribute('name')
			
		if ("<Errorfile " in line): 
			check_envirattr(line, '<Errorfile>','name')	
			PETRwriter.open_ErrorFile(check_attribute('name'),check_attribute('unique'))
			gotErrorfile = True

		if ("<Include " in line):
			check_envirattr(line, '<Include>','categories')	
			loclist = get_attribute('categories')
			ValidInclude = loclist.split()
			print '<Include> categories',ValidInclude
			if 'valid' in ValidInclude: 
				ValidOnly = True
				ValidInclude.remove('valid')
				
		if ("<Exclude " in line):
			check_envirattr(line, '<Exclude>','categories')	
			loclist = get_attribute('categories')
			ValidExclude = loclist.split()
			print '<Exclude> categories',ValidExclude
				
		if ("<Pause " in line):
			check_envirattr(line, '<Pause>','value')	
			theval = get_attribute('value')
			if 'lways' in theval: ValidPause = 1
			elif 'ever' in theval: ValidPause = -1
			else: ValidPause = 0
			
	PETRreader.close_FIN()
				
	if (len(PETRglobals.VerbFileName) == 0) or (len(PETRglobals.ActorFileList) == 0)  or (len(PETRglobals.AgentFileName) == 0):  
				print "Missing <Verbfile>, <AgentFile> or <ActorFile> in validation file <Environment> block",ErrMsgExitValidation
				sys.exit()

	if not gotErrorfile: 
		PETRwriter.open_ErrorFile()
	PETRwriter.write_ErrorFile('Validation file: ' + PETRglobals.TextFileList[0] + 
		'\nVerbs file: ' + PETRglobals.VerbFileName + '\nActors file: ' + 
		PETRglobals.ActorFileList[0] + '\n' + '\nAgents file: ' + 
		PETRglobals.AgentFileName + '\n')
	if len(ValidInclude): PETRwriter.write_ErrorFile('Include list: ' + ', '.join(ValidInclude)+'\n')
	if len(ValidExclude): PETRwriter.write_ErrorFile('Exclude list: ' + ', '.join(ValidExclude)+'\n')
	PETRwriter.write_ErrorFile('\n')
	PETRwriter.ErrorN += 0
	
	print 'Verb dictionary:',PETRglobals.VerbFileName
	PETRreader.read_verb_dictionary()
	print 'Actor dictionary:',PETRglobals.ActorFileList[0]
	PETRreader.read_actor_dictionary(PETRglobals.ActorFileList[0])
	print 'Agent dictionary:',PETRglobals.AgentFileName
	PETRreader.read_agent_dictionary()
	

# ================== TEXTFILE INPUT ================== #	


def get_NE(NPphrase):
# convert (NP...) ) to NE
# can raise UnbalancedTree, though that should have been hit before this
	nplist = ['(NE --- ']
	seg = NPphrase.split()
	if ShowNEParsing: print 'gNE',seg
	ka = 1
	while ka < len(seg):
		if seg[ka] == '(NEC':  # copy the phrase 
			nplist.append(seg[ka])
			ka += 1
			nparen = 1  # paren count
			while nparen > 0:
				if ka >= len(seg): raise_parsing_error('get_NE()-1')
				if seg[ka][0] == '(': nparen += 1
				elif seg[ka] == ')': nparen -= 1
				nplist.append(seg[ka])
#				print 'gNE1',nplist
				ka += 1
		elif seg[ka][0] == '(':
			if ka + 1 >= len(seg): raise_parsing_error('get_NE()-2')
			nplist.append(seg[ka+1])
			ka += 3
		else:
			nplist.append(')')
			ka += 1
			while ka < len(seg):
				nplist.append(seg[ka])
				ka += 1
			return nplist
			

def read_TreeBank():
# reads parsed sentence in the Penn TreeBank II format and puts the linearized version in  
# the list ParseList. Sets ParseStart, ParseEnd. Leaves global input file fin at line  
# following </parse>. Probably should do something with an EOF error
#
# This routine is supposed to be agnostic towards the line-feed and tab formatting of the 
# parse tree
# 
# can raise UnbalancedTree error

	""" ParseList coding
	Because they are still based in a shallow parsing approach, the KEDS/TABARI/PETR 
	dictionaries are based on linear string matching rather than a tree representation,
	which differs from the VRA and BBN approach, but is much faster. The information in
	the tree is used primarily for clause delineation and [via the Stanford system]
	co-referencing.
	
	The read_TreeBank() function is currently the "first line of defense" in modifying the 
	fully parsed input to a form that will work with the dictionaries developed under 
	the older shallow parser. As of <13.11.25> this is focused on converting noun 
	phrases ('(NP') to a shallower 'NE' (named-entity) format. Additional modifications
	may follow.
	
	Clauses are generally delineated using (XXX for the beginning and ~XXX for the end,
	where XXX are the TreeBank tags. The current code will leave some excess ')' at the
	end. 
	
	Additional markup:
	
	1. Simple noun phrases -- those which are delineated by '(NP ... '))' -- have their
		tag converted to 'NE' and the intermediate POS TreeBank marking removed. These 
		are the only phrases that can match actors and agents. A placeholder code '---' 
		is added to this structure.
		
		Note that because CoreNLP separates the two components of a possessive marking 
		(that is, noun + apostrophe-S), this cannot be used as part of an actor string,
		so for example
		       CHINA'S BLUEWATER NAVY
		is going to look like
		       CHINA 'S BLUEWATER NAVY
		In the rather unlikely case that the actor with and without the possessive would
		map to different code, do a global substitution, for example 'S -> QX and then
		match that, i.e.
		       CHINAQX BLUEWATER NAVY
		Realistically, however, a noun and its possessive will be equivalent in actor
		coding.
	   
	2. The possessive structure (NP (NP ... (POS )) ... ) is converted to an NE with the
		(POS 'S) eliminated, so this also cannot be in a dictionary
		
	3. The prepositional phrase structure (NP (NP ... )) (PP ) NP( ... )) is converted 
			to an NE; the preposition (IN ...) is retained 
			
	4. (VP and complex (NP are indexed so that the end of the phrase can be identified
			so these have the form (XXn and ~XXn
			
	Errors:
	
	ErrMsgUnbalancedTree: this is raised when the indices checking for clause boundaries
			go out of the bounds [0,len(treestr)-1]. In fact, a tree probably needs to
			be seriously off to get this far: it is much more likely that an unbalanced
			tree will just generate a nonsensical parse and probably just get skipped.
			But the program will keep running.	 			
		
	""" 
	
	""" <13.11.27> Reflections of PETR vs TABARI parsing
	As is well known, the shallow parsing of TABARI, while getting things wrong for the
	wrong reasons, also frequently got things right for the wrong reasons, which is to 
	say it was rather robust on variations, grammatical or otherwise, in the sentences.
	With the use of CoreNLP, we no longer have this advantage, and it is likely to take
	some coder experimentation with an extensive set of real texts to determine the 
	various contingencies that needs to be accommodated.
	
	At present, the special cases are handled though very specific code blocks. If enough
	of these accumulate, the code will be more maintainable if we can develop a general
	language for specifying these rules -- which should not be difficult given that the
	input from CoreNLP is well-structured -- but for the time being, we don't have enough
	rules to see what, if anything is needed. [Those rules might also leave the text with 
	balanced parentheses, as this is generally considered "a good thing"]
	
	""" 

	global ParseList, ParseStart, ParseEnd
	global treestr
	global ncindex   
	
	def get_forward_bounds(ka):
	# returns the bounds of a phrase in treestr that begins at ka, including  final space
	# can raise UnbalancedTree error
		global treestr #  <13.12.07> see note above
		kb = ka+1
		nparen = 1  # paren count
		while nparen > 0:
			if kb >= len(treestr):  raise_parsing_error('get_forward_bounds(ka)')
			if treestr[kb] == '(': nparen += 1
			elif treestr[kb] == ')': nparen -= 1
			kb += 1
		return [ka,kb] 

	def get_enclosing_bounds(ka):
	# returns the bounds of a phrase in treestr that encloses the phrase beginning at ka
	# can raise UnbalancedTree error
		global treestr #  <13.12.07> see note above
		kstart = ka-1
		nparen = 0  # paren count
		while nparen <= 0:  # back out to the phrase tag that encloses this
			if kstart < 0:  raise_parsing_error('get_enclosing_bounds(ka)')
			if treestr[kstart] == '(': nparen += 1
			elif treestr[kstart] == ')': nparen -= 1
			kstart -= 1
		return [kstart+1,get_forward_bounds(kstart+1)[1]]  

	def mark_compounds():
	# determine the inner-most phrase of each CC and mark:
	# NEC: compound noun phrase for (NP tags
	# CCP: compound phrase for (S and (VP tags [possibly add (SBAR to this?]
	# otherwise just leave as CC

		global treestr
		
		ka = -1
		while ka < len(treestr):
			ka = treestr.find('(CC',ka+3)  # 
			if ka < 0: break
			kc = treestr.find(')',ka+3)
			bds = get_enclosing_bounds(ka)
			kb = bds[0]
			if ShowMarkCompd: print '\nMC1:',treestr[kb:]
			if treestr[kb+1:kb+3] == 'NP':
				treestr = treestr[:kb+2] + 'EC' + treestr[kb+3:]  # convert NP to NEC
				if ShowMarkCompd: print '\nMC2:',treestr[kb:]
			if treestr[kb+2:kb+4] == 'VP' or treestr[kb+2:kb+4] == 'S ':
				treestr = treestr[:ka+3] + 'P' + treestr[ka+3:]   # convert CC to CCP
				if ShowMarkCompd: print '\nMC3:',treestr[kb:]
				
	def process_preposition(ka):
	# process (NP containing a (PP and return an nephrase: 
	# if this doesn't have a simple structure of  (NP (NP ...) (PP...) (NP/NEC ...)) 
	# without any further (PP -- i.e. multiple levels of prep phrases -- it returns a  
	# null string.
	
		global treestr, ncindex
		
		bds = get_enclosing_bounds(ka)  # this should be a (NP (NP
#		print 'PPP0: ',ka,bds[0],bds[1],treestr[bds[0]:bds[1]]
		if treestr.startswith('(NP (NP',bds[0]) :
			nepph = '(NP ' # placeholder: this will get converted 
			npbds = get_forward_bounds(bds[0]+4)  # get the initial (NP
			nepph += treestr[npbds[0]+4:npbds[1]-2] 
		elif treestr.startswith('(NP (NEC',bds[0]):
			nepph = '(NP (NEC ' # placeholder: 
			npbds = get_forward_bounds(bds[0]+4)  # get the initial (NEC
			nepph += treestr[npbds[0]+4:npbds[1] + 1] # save the closing ' ) '
		else:
#			print 'PPP0: no (NP (NP/(NEC' 
			return '' # not what we are expecting, so bail
#		print 'PPP1: ',nepph
		ka = treestr.find('(IN ',npbds[1])  # get the preposition and transfer it
		nepph += treestr[ka:treestr.find(' ) ',ka+3) + 3] 
#		print 'PPP2: ',nepph, '\n     ',ka,bds[1],treestr[ka+4:bds[1]]
		kp = treestr.find('(NP ',ka+4,bds[1]) # find first (NP or (NEC after prep
		kec = treestr.find('(NEC ',ka+4,bds[1])
		if kp <  0 and kec < 0: 
#			print 'PPP2a: No NP or NEC'
			return '' # not what we are expecting, so bail
		if kp <  0:  kp = len(treestr)  # no (NP gives priority to (NEC and vice versa
		if kec <  0: kec = len(treestr)
		if kp < kec:  
			kb = kp
#			print 'PPP2a: got NEC', treestr[kb:]
		else:
			kb = kec
#		 	print 'PPP2a: got NP', treestr[kb:]
		npbds = get_forward_bounds(kb)  # 
		if '(PP' in treestr[npbds[0]:npbds[1]]: 
#			print 'PPP2b: Embedded (PP'			 
			return '' # there's another level of (PP here
		if treestr[kb+2] == 'E': # leave the (NEC in place. <14.01.15> It should be possible to add an index here, right?			
			nepph += treestr[kb :npbds[1] + 3 ] # pick up two ') '
		else: nepph += treestr[npbds[0]+4 :npbds[1] + 1 ] # skip the (NP and pick up the final ' ' (we're using this to close the original (NP
		exst = '\"'+ nepph + '\"'  # add quotes to see exactly what we've got here
#		print 'PPP3: ',exst
		return nepph

				
	fullline = '' 
	vpindex = 1
	npindex = 1
	ncindex = 1  
	treestr = ''
	line = PETRreader.read_FIN_line() 
	while '</Parse>' not in line: 
		line = line.strip() + ' '
		line = line.replace(')',' ) ')
		treestr += line.upper()
		line = PETRreader.read_FIN_line() 
#	print 'RT1:', treestr # debug

	mark_compounds()
	
	ka = 0
	while ka < len(treestr):
		if treestr.startswith('(NP ',ka):
			npbds = get_forward_bounds(ka)
			nephrase = ''
			if ShowNEParsing: print 'BBD: ',treestr[npbds[0]:npbds[1]]
			if '(POS'  in treestr[ka+3:npbds[1]]: # get the (NP possessive
				kb = treestr.find('(POS',ka+4)
				nephrase = treestr[ka+4:kb-1]  # get string prior to (POS
				nephrase += ' ' + treestr[kb+12:npbds[1]] # skip over (POS 's) and get the remainder of the NP
				if ShowNEParsing: print 'RTPOS: NE:',nephrase
				
			elif '(PP'  in treestr[ka+3:npbds[1]] :  #  prepositional phrase	
#				print 'PPP-1: ',treestr[ka:npbds[1]]
#				print 'PPP-1a: ',treestr.find('(PP',ka+3,npbds[1]),ka,npbds[1]
#				print 'PPP-1a: ',get_enclosing_bounds(treestr.find('(PP',ka+3,npbds[1]))
				nephrase = process_preposition(treestr.find('(PP',ka+3,npbds[1]))  
				if ShowNEParsing: print 'RTPREP: NE:',nephrase
				
			elif '(NP' not in treestr[ka+3:npbds[1]] and '(NEC' not in treestr[ka+3:npbds[1]]: # no further (NPs, so convert to NE
				nephrase = treestr[ka:npbds[1]]  
				if ShowNEParsing: print 'RTNP: NE:',nephrase
			
			if len(nephrase) > 0:
				nplist = get_NE(nephrase)
				if not nplist: raise_parsing_error('read_TreeBank()-1')  # <14.02.27> Seems like an odd place to hit this error, and it will probably go away...
				for kb in range(len(nplist)): fullline += nplist[kb] + ' '
				ka = npbds[1] + 1				
			else:  # it's something else...
				fullline += '(NP' + str(npindex)	+ ' '  # add index
				npindex += 1
				ka += 4
				
		elif treestr.startswith('(NEC ',ka) : 
			"""
			assign indices inside a compound, which may involve just a simple (NNP or (NNS
			also eliminates the internal commas and compound, leaving just the NE.
					
			Parsing bug note: <14.01.13>
			In what appear to be rare circumstances, CoreNLP does not correctly delimit two
			consecutive nouns in a compound as (NP. Specifically, in the test sentence 
		
					Mordor and the Shire welcomed a resumption of formal diplomatic ties 
					between Minas Tirith and Osgiliath. 
				
			the second compound phrase is marked as 
		
				 (NP (NNP Minas) (NNP Tirith) (CC and) (NNP Osgiliath))
		
			but if "Osgiliath" is changed to "Hong Kong" it gives the correct
		
				 (NP (NP (NNP Minas) (NNP Tirith)) (CC and) (NP (NNP Hong) (NNP Kong))
			 
			A systematic check of one of the GigaWord files shows that this appears to occur 
			only very rarely -- and in any case is a parsing error -- so this routine 
			does not check for it.  
			"""

			parts = line.partition('(NEC')
			fullline += '(NEC' + str(ncindex) +  ' '
			ncindex += 1
			necbds = get_forward_bounds(ka)  # get the bounds of the NEC phrase
			if ShowMarkCompd: print 'RTBD: NE:',necbds
			ka += 4
			while ka < necbds[1]:  # convert all of the NP, NNS and NNP to NE
#				print treestr[ka:necbds[1]]
				if treestr.startswith('(NP',ka) or treestr.startswith('(NN',ka):
					npbds = get_forward_bounds(ka)
					if ShowMarkCompd: print 'RTBD1: NE:',npbds, treestr[npbds[0]:npbds[1]]
					if treestr.startswith('(NN',ka): # just a single element, so get it 
						seg = treestr[npbds[0]:npbds[1]].split()
						nplist = ['(NE --- ', seg[1],' ) ']
					else: nplist = get_NE(treestr[npbds[0]:npbds[1]])
					if ShowMarkCompd: print 'RTBD2: NE:',nplist
					for kb in range(len(nplist)): fullline += nplist[kb] + ' '
					ka = npbds[1]
				ka += 1
			fullline += ' ) '  # closes the nec
			if ShowMarkCompd: print 'RTBD3: NE:',fullline
			ka = necbds[1] + 1
			
		elif treestr.startswith('(VP ',ka) : # assign index to VP
			parts = line.partition('(VP')
			fullline += '(VP' + str(vpindex) +  ' '
			vpindex += 1
			ka += 4
		else: 
			fullline += treestr[ka]	
			ka += 1	

	# convert the text to ParseList format; convert ')' to ~XX tags
	ParseList = fullline.split() 
#	print '<<',ParseList
	ka = 0
	opstack = []
	while ka < len(ParseList):
		if ParseList[ka][0] == '(': 
			opstack.append(ParseList[ka][1:])
		if ParseList[ka][0] == ')':
			if len(opstack) == 0: break
			op = opstack.pop()
#			print '<<',op
			ParseList[ka] = '~'+op
		ka += 1
				
#	print 'RT2:',ParseList
	ParseStart = 2
	ParseEnd = len(ParseList) - 5  # should skip final punctuation, -S, -ROOT

				
				
# ================== CODING ROUTINES  ================== #	

def get_loccodes(thisloc):
# returns the list of codes from a compound, or just a single code if not compound
	global UpperSeq, LowerSeq
	codelist = []
#	print 'GLC0',thisloc
	if thisloc[1]: 
		try: neitem = UpperSeq[thisloc[0]]
		except IndexError: raise_parsing_error('get_loccodes()-1') # at this point some sort of markup we can't handle, not necessarily unbalanced 

#		print 'GLC1',neitem
		if '(NEC' in neitem: # extract the compound codes from the (NEC ... ~NEC sequence 
			ka = thisloc[0]-1  # UpperSeq is stored in reverse order
			while '~NEC' not in UpperSeq[ka]:
#				print 'GLC2',ka, UpperSeq[ka]
				if '(NE' in UpperSeq[ka]: 
					codelist.append(UpperSeq[ka][UpperSeq[ka].find('>')+1:])
				ka -= 1
				if ka < 0: raise_parsing_error('get_loccodes()-2') # at this point some sort of markup we can't handle, not necessarily unbalanced 

		else: codelist.append(neitem[neitem.find('>')+1:]) # simple code
	else:
		try: neitem = LowerSeq[thisloc[0]]
		except IndexError: raise_parsing_error('get_loccodes()-3') # at this point some sort of markup we can't handle, not necessarily unbalanced 
#		print 'GLC3',neitem
		if '(NEC' in neitem: # extract the compound codes
			ka = thisloc[0]+1
			while '~NEC' not in LowerSeq[ka]:
#				print 'GLC4',ka, LowerSeq[ka]
				if '(NE' in LowerSeq[ka]: 
					codelist.append(LowerSeq[ka][LowerSeq[ka].find('>')+1:])
				ka += 1
				if ka >= len(LowerSeq): raise_parsing_error('get_loccodes()-4') # at this point some sort of markup we can't handle, not necessarily unbalanced 

		else: codelist.append(neitem[neitem.find('>')+1:])
#	print 'GLC5',codelist
	return codelist

def find_source():
# assign SourceLoc to the first coded or compound (NE in the UpperSeq; if neither found
# then first (NE with --- code 
# <13.12.07>: this is going to change, right: we just get the correct (NE 
# note that we are going through the sentence in normal order, so we go through UpperSeq
# in reverse order. 
# Also note that this matches either (NE and (NEC: this is resolved in make_event_string
	global 	UpperSeq, SourceLoc
#	print "FS-1"
	kseq = len(UpperSeq) - 1
	while kseq >= 0 :
		if ('(NEC' in UpperSeq[kseq]) : 
			SourceLoc = [kseq, True]
			return
		if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]): 
			SourceLoc = [kseq, True]
			return
		kseq -= 1
								# failed, so check for uncoded source	
	kseq = len(UpperSeq) - 1
	while kseq >= 0 :
		if ('(NE' in UpperSeq[kseq]): 
			SourceLoc = [kseq, True]
			return
		kseq -= 1	

def find_target():
# Assign TargetLoc 
	""" Priorities for assigning target:
		1. first coded (NE in LowerSeq that does not have the same code as SourceLoc; 
		    codes are not checked with either SourceLoc or the candidate target are 
		    compounds (NEC
		2. first null-coded (NE in LowerSeq ; 
		3. first coded (NE in UpperSeq -- that is, searching backwards from the verb --
		   that does not have the same code as SourceLoc; 
		4. first null-coded (NE in UpperSeq 
	"""

	global UpperSeq, LowerSeq, SourceLoc, TargetLoc
	srccodelist = get_loccodes(SourceLoc)
	if len(srccodelist) == 1:
		srccode = '>' + srccodelist[0]
	else: srccode = '>>>>' # placeholder for a compound; this will not occur
#	print 'FT-1: srccode',srccode
	kseq = 0
	while kseq < len(LowerSeq) :
		if ('(NE' in LowerSeq[kseq]) and ('>---' not in LowerSeq[kseq]):
			if (srccode not in LowerSeq[kseq]):
				TargetLoc = [kseq, False]
				return
		kseq += 1
								# failed, so check for uncoded target in LowerSeq	
	kseq = 0
	while kseq < len(LowerSeq) :
		if ('(NE' in LowerSeq[kseq]) and ('>---' in LowerSeq[kseq]): # source might also be uncoded now
			TargetLoc = [kseq, False]
			return
		kseq += 1

	# still didn't work, so look in UpperSeq going away from the verb, so we increment through UpperSeq
	kseq = 0
	while kseq < len(UpperSeq)  :
		if ('(NE' in UpperSeq[kseq]) and ('>---' not in UpperSeq[kseq]): 
			if (srccode not in UpperSeq[kseq]):
				TargetLoc = [kseq, True]
				return
		kseq += 1
								# that failed as well, so finally check for uncoded target	
	kseq = 0
	while kseq < len(UpperSeq)  :
		if ('(NE' in UpperSeq[kseq]) and ('>---' in UpperSeq[kseq]): 
			if (kseq != SourceLoc[0]):  # needs to be a different (NE from source 
				TargetLoc = [kseq, True]
				return
		kseq += 1
				
def make_check_sequences(verbloc, endtag):
# create the upper and lower sequences to be checked by the verb patterns based on the 
# verb at ParseList[verbloc]. Lower sequence includes only words in the VP 
# Upper sequence currently terminated by ParseStart, ~S or ~,
#
	""" Note-1: Adding location and code information to (NE
	<13.11.15>
	The trade-off here is storing this as text, which involves the cost of str{kword)
	vs storing the information in a list, which means we need something more complex
	then "if ('(NE'..." to check for it...that is, *Seq now contains multiple data
	types. My logic here is that the *Seq lists are potentially evaluated a large 
	number of times, whereas the text only needs to be decoded when a pattern in 
	matched, but that could be wrong.
	Hmmm, do we really need the location, or just the code? Getting the code is cheap  
	"""
	global ParseList, ParseStart, ParseEnd
	global UpperSeq, LowerSeq

	# generate the upper sequence: note that this is in reverse word order
	UpperSeq = []
	kword = verbloc - 1
	while kword >= ParseStart:
#		if ('~S' in ParseList[kword]) or ('~,' in ParseList[kword]): break
		if ('~,' in ParseList[kword]): break
		if ('(NE' == ParseList[kword]):
			code = UpperSeq.pop()  # remove the code
			UpperSeq.append(ParseList[kword]+'<'+str(kword)+'>'+code)  # <pas 13.07.26> See Note-1 
		elif ('NEC' in ParseList[kword]):
			UpperSeq.append(ParseList[kword])
		elif ('~NE' in ParseList[kword]):
			UpperSeq.append(ParseList[kword])
		elif (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
			UpperSeq.append(ParseList[kword])
		kword -= 1

	if ShowCodingSeq: print "Upper sequence:",UpperSeq
#	for alist in UpperSeq: print alist  # debug
		
	# generate the lower sequence
	LowerSeq = []
	kword = verbloc + 1
	while (endtag not in ParseList[kword]):  # limit this to the verb phrase itself
		if ('(NE' == ParseList[kword]):
			LowerSeq.append(ParseList[kword]+'<'+str(kword)+'>'+ParseList[kword+1])  # <pas 13.07.26> See Note-1 
			kword += 1  # skip code
		elif ('NEC' in ParseList[kword]):
			LowerSeq.append(ParseList[kword])
		elif ('~NE' in ParseList[kword]):
			LowerSeq.append(ParseList[kword])
		elif (ParseList[kword][0] != '(') and (ParseList[kword][0] != '~'):
			LowerSeq.append(ParseList[kword])
		kword += 1
		if kword >= ParseEnd: 
			raise_parsing_error('make_check_sequences()') # at this point some sort of markup we can't handle, not necessarily unbalanced 
			return   


	if ShowCodingSeq: print "Lower sequence:",LowerSeq
#	for alist in LowerSeq: print alist  # debug
				

def verb_pattern_match(patlist, aseq, isupperseq):
# attempts to match patlist against UpperSeq or LowerSeq; returns True on success
# Can set SourceLoc and TargetLoc for $, + and % tokens
# Still need to handle %

	def find_ne(kseq):
	# return the location of the (NE element in aseq starting from kseq, which is inside an NE 
		ka = kseq
		while '(NE' not in aseq[ka]: 
			if isupperseq: ka += 1
			else: ka -= 1
			if ka < 0 or ka >= len(aseq):
				raise_parsing_error('find_ne(kseq) in verb_pattern_match()') # at this point some sort of markup we can't handle, not necessarily unbalanced 

		return ka
	
	global SourceLoc, TargetLoc
#	print "VPM-1" , patlist, aseq   # debug
	if len(patlist) == 0 : return True  # nothing to evaluate, so okay
	if len(aseq) == 0 : return False    # nothing to match, so fails
	insideNE = False
	kpatword = 1  # first word, skipping connector
	kseq = 0	
	while kpatword < len(patlist):  # iterate over the words in the pattern
		if ('~NE' in aseq[kseq]) or ('(NE' in aseq[kseq]): 
			kseq += 1
			if kseq >= len(aseq): return False  # hit end of sequence before full pattern matched
			insideNE = not insideNE
		if len(patlist[kpatword]) == 1:  # deal with token assignments here
			if insideNE: 
				if patlist[kpatword] == '$': SourceLoc = [find_ne(kseq),isupperseq]
				if patlist[kpatword] == '+': TargetLoc = [find_ne(kseq),isupperseq]
				elif patlist[kpatword] == '%': pass # deal with compound
#				print "VPM-4: Token assignment " , patlist[kpatword], aseq[find_ne(kseq)]   # debug
				kpatword += 2  # skip connector
				if kpatword >= len(patlist): return True
				kseq += 1
				if kseq >= len(aseq): return False  
			elif patlist[kpatword-1] == ' ': 
				kseq += 1
				if kseq >= len(aseq): return False  	
			else: return False
		elif patlist[kpatword] != aseq[kseq]:
#			print "VPM-2: Fail " , patlist[kpatword], aseq[kseq]   # debug
			if patlist[kpatword-1] == ' ': 
				kseq += 1
				if kseq >= len(aseq): return False  
			else: return False
		else:  # match successful to this point
#			print "VPM-3: Match " , patlist[kpatword], aseq[kseq]   # debug
			kpatword += 2  # skip connector
			if kpatword >= len(patlist): return True
			kseq += 1
			if kseq >= len(aseq): return False  
	return True  # complete pattern matched (I don't think we can ever hit this)

  
def check_verbs():
# primary coding loop which looks for verbs, checks whether any of their patterns match,
# then fills in the source and target if there has been a match. Stores events in
# EventList.
	""" SourceLoc, TargetLoc structure
	
	[0]: the location in *Seq where the NE begins
	[1]: True - located in UpperSeq, otherwise in LowerSeq
	"""
	global EventCode, SourceLoc, TargetLoc
	global EventList
	EventList = []
	SourceLoc = [-1,True] ; TargetLoc = [-1,True]  
	kitem = ParseStart
	while kitem < ParseEnd:
		if ('(VP' in ParseList[kitem]) and ('(VB' in ParseList[kitem+1]):
			targ = ParseList[kitem+2] + ' '
			if targ in PETRglobals.VerbDict:
					if ShowPattMatch: print "CV-1 Found", targ
					endtag = '~VP' +  ParseList[kitem][3:]
					hasmatch = False
					make_check_sequences(kitem+2, endtag)
					if PETRglobals.VerbDict[targ][0]:
						patternlist = PETRglobals.VerbDict[targ]
					else:
						patternlist = PETRglobals.VerbDict[PETRglobals.VerbDict[targ][1]]  # redirect from a synonym
					kpat = 2
					if ShowPattMatch: print "CV-2 patlist", patternlist
					while kpat < len(patternlist):
						SourceLoc = [-1,True] ; TargetLoc = [-1,True]  
						if verb_pattern_match(patternlist[kpat][0], UpperSeq, True):
							if verb_pattern_match(patternlist[kpat][1], LowerSeq, False):
								if ShowPattMatch: print "Found a pattern match"   # debug
								EventCode = patternlist[kpat][2]
								hasmatch = True
								break
						kpat += 1
					if not hasmatch and patternlist[1] != '---':
						if ShowPattMatch: print "Matched on the primary verb"   # debug
						EventCode = patternlist[1]
						hasmatch = True

					if hasmatch:
						if SourceLoc[0] < 0: find_source()
						if ShowPattMatch: print "CV-3 src", SourceLoc						
						if SourceLoc[0] >= 0: 
							if TargetLoc[0] < 0: find_target()
							if TargetLoc[0] >= 0: 
								if ShowPattMatch: print "CV-3 tar", TargetLoc						
								make_event_strings()

					if hasmatch: 
						while (endtag not in ParseList[kitem]): kitem +=1 # resume search past the end of VP
		kitem += 1


def get_actor_code(index):
# date restrictions need to be added here
	for item in PETRglobals.ActorCodes[index]:
		if len(item) == 1: 
#			print "GAC-1",index, item[0]  # debug
			return item[0]
	# no unrestricted code, so just use the first one;
	# replace this with date restriction resolution
#	print "GAC-2",index, PETRglobals.ActorCodes[index][0][-1]  # debug
	return PETRglobals.ActorCodes[index][0][-1]


def actor_phrase_match(patphrase, phrasefrag):
# determines whether the actor pattern occurs in phrasefrag
# returns True if match is successful. Insha'Allah...
#	APMprint = True   # yes, kept having to come back to debug this...
	APMprint = False
	connector = patphrase[1]
	kfrag = 1   # already know first word matched
	kpatword = 2  # skip code and connector
	if APMprint: print "APM-1",len(patphrase), patphrase,"\nAPM-2",len(phrasefrag), phrasefrag  # debug
	if len(patphrase) == 2:
		if APMprint: print "APM-2.1: singleton match"   # debug
		return True # root word is a sufficient match
	if len(patphrase) == 3 and patphrase[2][0] == "":   # <14.02.28>: these both do the same thing, except one handles a string of the form XXX and the other XXX_. This is probably unnecessary. though it might be...I suppose those are two distinct cases. 
		if APMprint: print "APM-2.2: singleton match"   # debug
		return True # root word is a sufficient match
	if kfrag >= len(phrasefrag): return False     # end of phrase with more to match
	while kpatword < len(patphrase):  # iterate over the words in the pattern
		if APMprint: print "APM-3", kfrag, kpatword,"\n  APM Check:",kpatword, phrasefrag[kfrag], patphrase[kpatword][0]  # debug
		if phrasefrag[kfrag] == patphrase[kpatword][0]:  
			if APMprint: print "  APM match"  # debug
			connector = patphrase[kpatword][1]
			kfrag += 1
			kpatword += 1
			if kpatword >= len(patphrase):	return True  # complete pattern matched
		else: 
			if APMprint: print "  APM fail"  # debug
			if connector == '_': return False  # consecutive match required, so fail
			else:
				kfrag += 1  # intervening words are allowed
		if kfrag >= len(phrasefrag): return False     # end of phrase with more to match
	return True  # complete pattern matched (I don't think we can ever hit this)

def check_NEphrase(nephrase):
	"""
	This function tries to find actor and agent patterns matching somewhere in the phrase.
	The code for the first actor in the phrase is used as the base; there is no further
	search for actors
	
	All agents with distinct codes that are in the phrase are used -- including phrases 
	which are subsets of other phrases (e.g. 'REBEL OPPOSITION GROUP [ROP]' and 
	'OPPOSITION GROUP' [OPP]) and they are appended in the order they are found. If an 
	agent generates the same 3-character code (e.g. 'PARLIAMENTARY OPPOSITION GROUP [OOP]'  
	and 'OPPOSITION GROUP' [OPP]) the code is appended only the first time it is found.
	
	Note: In order to avoid accidental matches across codes, this checks in increments 
	of 3 character blocks. That is, it assumes the CAMEO convention where actor and agent 
	codes are usually 3 characters, occasionally 6 or 9, but always multiples of 3.
	"""

	kword = 0
	actorcode = ""
	if ShowNEParsing: print "CNEPh initial phrase",nephrase # debug
	while kword < len(nephrase):  # iterate through the phrase looking for actors
		phrasefrag = nephrase[kword:]
		if ShowNEParsing: print "CNEPh Actor Check",phrasefrag[0]  # debug
		if phrasefrag[0] in PETRglobals.ActorDict:  # check whether patterns starting with this word exist in the dictionary
			if ShowNEParsing: print "                Found",phrasefrag[0]  # debug
			patlist = PETRglobals.ActorDict[nephrase[kword]]
#			print "CNEPh Mk1:",patlist
			for index in range(len(patlist)): # iterate over the patterns beginning with this word
				if actor_phrase_match(patlist[index], phrasefrag): 
					actorcode = get_actor_code(patlist[index][0])   # found a coded actor
#					print "CNEPh Mk2:",actorcode
					break
		if len(actorcode) > 0: break   # stop after finding first actor
		else: kword += 1

	kword = 0
	agentlist = []
	while kword < len(nephrase):  # now look for agents
		phrasefrag = nephrase[kword:]
		if ShowNEParsing: print "CNEPh Agent Check",phrasefrag[0]  # debug
		if phrasefrag[0] in PETRglobals.AgentDict:  # check whether patterns starting with this word exist in the dictionary
			if ShowNEParsing: print "                Found",phrasefrag[0]  # debug
			patlist = PETRglobals.AgentDict[nephrase[kword]]
			for index in range(len(patlist)): # iterate over the patterns beginning with this word
				if actor_phrase_match(patlist[index], phrasefrag): 
					agentlist.append(patlist[index][0])   # found a coded actor
					break
		kword += 1   # continue looking for more agents
		
	if len(agentlist) == 0: 
		if len(actorcode) == 0: return [False]  # no actor or agent
		else: return [True,actorcode]  # actor only
		
	if len(actorcode) == 0: actorcode = '---'   # unassigned agent
	
	for agentcode in agentlist: # assemble the composite code
		if agentcode[0] == '~': agc = agentcode[1:]  # extract the code
		else: agc = agentcode[:-1]
		aglen = len(agc) # set increment to the length of the agent code
#		print aglen, actorcode, agentcode, agc
		ka = 0  # check if the agent code is already present
		while ka < len(actorcode) - aglen + 1:
			if agc == actorcode[ka:ka+aglen]:
				ka = -1  # signal duplicate
				break
			ka += 3
		if ka < 0: break
		if agentcode[0] == '~': actorcode += agc
		else: actorcode = agc + actorcode
	return [True,actorcode]


def assign_NEcodes():
# assigns non-null codes to NE phrases where appropriate
	def expand_compound_element(kstart):  
		# this is almost but not quite a recursive call on expand_compound_NEPhrase():
		# this difference is that the (NEC has already been established so we are just adding
		# elements inside the list and there is no further check: we're not allowing any 
		# further nesting of compounds. That could doubtlessly be done fairly easily with some 
		# possibly too-clever additional code but such constructions are virtually unknown in 
		# actual news stories. 
		global ParseList

		try:
			kend = ParseList.index('~NE',kstart)
		#	print 'exCel1:', ParseList[kstart:kend]
			ncstart = ParseList.index('(NEC',kstart,kend)
			ncend = ParseList.index('~NEC',ncstart,kend)
		except ValueError:
			raise_parsing_error('expand_compound_element()') # at this point some sort of markup we can't handle, not necessarily unbalanced 
			return   
			
		prelist = ParseList[kstart+1:ncstart]  # first element is always '(NE'
		postlist = ParseList[ncend+1:kend]
	#	print 'exCel2:\n **',prelist,'\n **',ParseList[ncstart:ncend+1],'\n **',postlist
		newlist = []
		ka =ncstart + 1
		while ka < ncend-1:  # convert all of the NP, NNS and NNP to NE
	#				print treestr[ka:necbds[1]]
			if '(N' in ParseList[ka] :  # any TreeBank (N* tag is legitimate here
				endtag = '~' + ParseList[ka][1:]
				itemlist = ['(NE','---']
				itemlist.extend(prelist)
				ka += 1
				while ParseList[ka] != endtag:
					itemlist.append(ParseList[ka])
					ka += 1
				itemlist.extend(postlist)
				itemlist.append('~NE')
				newlist.extend(itemlist)
	#			print 'exCel3:',newlist
			ka += 1  # okay to increment since next item is (, or (CC
		ParseList = ParseList[:kstart] + newlist + ParseList[kend+1:] 
	#	print 'exCel4:',ParseList
		return kstart+len(newlist)
			
	def expand_compound_NEPhrase(kstart,kend):  
		# Expand the compound phrases inside an (NE: this replaces these with a list of NEs 
		# with the remaining text simply duplicated. Code and agent resolution will then
		# be done on these phrases as usual. This will handle two separate (NECs, which is 
		# as deep as one generally encounters.
		global ParseList
	#	print 'exNEp0:', ParseList[kstart:kend]
		ncstart = ParseList.index('(NEC',kstart,kend)
		ncend = ParseList.index('~NEC',ncstart,kend)
		prelist = ParseList[kstart+1:ncstart-1]  # first element is always '---'
		postlist = ParseList[ncend+1:kend]
	#	print 'exNEp1:\n --',prelist,'\n --',ParseList[ncstart:ncend+1],'\n --',postlist
		newlist = ['(NEC']
		ka =ncstart + 1
		while ka < ncend-1:  # convert all of the NP, NNS and NNP to NE
	#				print treestr[ka:necbds[1]]
			if '(N' in ParseList[ka] :
				endtag = '~' + ParseList[ka][1:]  
				itemlist = ['(NE']
				itemlist.extend(prelist)
				ka += 1
				while ParseList[ka] != endtag:
					itemlist.append(ParseList[ka])
					ka += 1
				itemlist.extend(postlist)
				itemlist.append('~NE')
				newlist.extend(itemlist)
	#			print 'exNEp2:',newlist
			ka += 1  # okay to increment since next item is (, or (CC
		newlist.append('~NEC')
		newlist.append('~TLTL')  # insert a tell-tale here in case we need to further expand this
		ParseList = ParseList[:kstart] + newlist + ParseList[kend+1:] 
	#	print 'exNEp3:',ParseList
		if '(NEC' in newlist[1:-1]:  # expand next set of (NEC if it exists
			ka = kstart + 1
	#		print 'exNEp4:', ParseList[ka: ParseList.index('~TLTL',kstart)]	
			while '(NE' in ParseList[ka:ParseList.index('~TLTL',ka)]:
				ka = expand_compound_element(ka)
	#			print 'exNEp5:', ParseList[ka: ParseList.index('~TLTL',ka)]	

		ParseList.remove('~TLTL')  # tell-tale is no longer needed

	global ParseStart, ParseEnd, ParseList
	global nephrase

	kitem = ParseStart
	while kitem < ParseEnd:
		if '(NE' == ParseList[kitem]:
			nephrase = []
			kstart = kitem
			kcode = kitem + 1
			kitem += 2 # skip NP, code,
			if kitem >= len(ParseList): 
				raise_parsing_error('assign_NEcodes()-0') # at this point some sort of markup we can't handle, not necessarily unbalanced 
				return   
			while  '~NE' != ParseList[kitem]:
				if ParseList[kitem][1:3] != 'NN':   # <14.01.15> At present, read_TreeBank can leave (NNx in place in situations involving (PP and (NEC: so COMPOUND-07. This is a mildly kludgy workaround that insures a check_NEphrase gets clean input
					nephrase.append(ParseList[kitem])
				kitem += 1
				if kitem >= len(ParseList): 
					raise_parsing_error('assign_NEcodes()-1') # at this point some sort of markup we can't handle, not necessarily unbalanced 
					return   
			if ShowNEParsing: print "aNEc",kcode,":", nephrase   # debug
			if '(NEC' in nephrase:
				expand_compound_NEPhrase(kstart,kitem)
				kitem = kstart - 1  # process the (NEs following the expansion
			else:
				result = check_NEphrase(nephrase)
				if result[0]:
					ParseList[kcode] = result[1]
					if ShowNEParsing: print "Assigned",result[1]   # debug
		kitem += 1
		if kitem >= len(ParseList): 
			raise_parsing_error('assign_NEcodes()-2') # <14.02.27> so for this to be hit, somehow ParseEnd isn't correct: why?

def make_event_strings():
# creates the set of event strings, handing compound actors and symmetric events
	global SentenceLoc
	global EventCode, SourceLoc, TargetLoc
	global CodedEvents
	
	def make_events(codessrc, codestar, codeevt):
	# create events from each combination in the actor lists except self-references
		global CodedEvents
		global SentenceLoc
		for thissrc in codessrc:
			cursrccode = thissrc
			if thissrc[0:3] == '---' and len(SentenceLoc) > 0: cursrccode = SentenceLoc + thissrc[3:] # add location if known
			for thistar in codestar:
				if thissrc != thistar:  # skip self-references
					curtarcode = thistar
					if thistar[0:3] == '---' and len(SentenceLoc) > 0: curtarcode = SentenceLoc + thistar[3:] # add location if known
					CodedEvents.append([cursrccode,curtarcode,codeevt])		

	def expand_compound_codes(codelist):
	# expand coded compounds, that is, codes of the format XXX/YYY
		for ka in range(len(codelist)): 
			if '/' in codelist[ka]:
				parts = codelist[ka].split('/')
	#			print 'MES2:', parts  # debug
				kb = len(parts) - 2   # this will insert in order, which isn't necessary but might be helpful
				codelist[ka] = parts[kb+1]
				while kb >= 0:
					codelist.insert(ka,parts[kb])
					kb -= 1

#	print 'MES1: ',SourceLoc, TargetLoc
	srccodes = get_loccodes(SourceLoc)
	expand_compound_codes(srccodes)
	tarcodes = get_loccodes(TargetLoc)
	expand_compound_codes(tarcodes)
			
#	print 'MES2: ',srccodes, tarcodes, EventCode
	if len(srccodes) == 0 or len(tarcodes) == 0:
		PETRwriter.write_record_error('Empty codes in make_event_strings()')   # <14.02.27> This is here temporarily (ha!) to just get this thing to handle timing tests (and in the presence of some known bugs): this should not be a persistent issue. Really
		return		 
	
	if ':' in EventCode:  # symmetric event
		if srccodes[0] == '---' or tarcodes[0] == '---':
		  if  tarcodes[0] == '---': tarcodes = srccodes  # <13.12.08> Is this behavior defined explicitly in the manual??? 
		  else: srccodes = tarcodes   
		ecodes = EventCode.partition(':')
#		print 'MES3: ',ecodes
		make_events(srccodes, tarcodes, ecodes[0])
		make_events(tarcodes, srccodes, ecodes[2])
	else: make_events(srccodes, tarcodes, EventCode)
	
	# remove duplicates
	ka = 0
	while ka < len(CodedEvents)-1:  # need to evaluate the bound every time through the loop
		kb = ka + 1
		while kb < len(CodedEvents):
			if CodedEvents[ka] == CodedEvents[kb]: del CodedEvents[kb]
			kb += 1
		ka += 1
	
#	print "MES exit:",CodedEvents
	return 
				
# ========================== PRIMARY CODING FUNCTIONS ========================== #	
	
def reset_event_list(firstentry = False):
# set the event list and story globals for the current story or just intialize if firstentry
# probably should replace the magic numbers -6:-3 here and in do_coding
	global SentenceDate, StoryDate, SentenceSource, StorySource 
	global SentenceID, CurStoryID, SkipStory
	global StoryEventList, StoryIssues 
	global NStory

	StoryEventList = []
	if PETRglobals.IssueFileName != "": StoryIssues = {}

	SkipStory = False
	if firstentry: 
		CurStoryID = ''
	else:
		CurStoryID = SentenceID[-6:-3]
		StoryDate = SentenceDate
		StorySource = SentenceSource
		NStory += 1
#	print 'CurStoryID',CurStoryID
	
def read_record():
	"""
	Reads an input record, and directly sets SentenceText and SentenceSource; various 
	other sentence globals (e.g. SentenceDate, SentenceID, ParseList ) are set by routines
	called from here.
	
	Raises StopCoding if <Stop> found
	PETRreader.read_FIN_line() can raise EOFError; this is passed through

	PETR organizes records into 'stories' and 'sentences' using the final six characters
	of the id field. These are assumed to be of the form NNN-SS where NNN are the final
	three digits of the story ID and SS is the sentence order. At present, the system 
	just uses NNN -- that is, the ID[-6:-3] slice -- to determine when a new story has
	been encountered, but the SS is useful for determining lede and HLEAD sentences.
	
	At present, the 'story' identification is used in two features
	 -- Tuple filtering is used within the story
	 -- A +<string> in the Discards file skips the entire story when the string is 
	    found
	"""
	global SentenceDate, SentenceText, SentenceID, SentenceSource
	global NSent

	SentenceSource = ''
	line = PETRreader.read_FIN_line() 
	while line: 
#		print line
		if ('<Sentence ' in line): 
			try : extract_Sentence_info(line)
			except MissingAttr: 
				print 'Skipping sentence: Missing date field in',line,
				return  # let SkipRecord be caught by calling routine
			NSent += 1
			### debug
			SentenceID = SentenceID[:-1]+'0'+SentenceID[-1]  # add zero to match the new format
#			print SentenceID
			### debug
							
			
		if ('<Source ' in line): # need to substitute something more robust here
			extract_attributes(line)
			SentenceSource = check_attribute('id')
			
		if ('<Text>' in line): 
			SentenceText = ''
			line = PETRreader.read_FIN_line()
			while '</Text>' not in line:
				SentenceText += line[:-1]
				if ' ' not in SentenceText[-1]: SentenceText += ' '
				line = PETRreader.read_FIN_line()
				
		if ('<Stop>' in line): 
			raise StopCoding
			return  # let StopCoding be caught by calling routine
			
		if '<Parse>' in line:
			try: 
				read_TreeBank()
				break
			except UnbalancedTree: # without the 'break', this will just skip processing the record and go to the next one
				PETRwriter.write_record_error(ErrMsgUnbalancedTree, SentenceID,SentenceCat) 
			except EOFError: raise 
		
		line = PETRreader.read_FIN_line()

	if not line: raise EOFError
	print '\nSentence:',SentenceDate, SentenceID
	print SentenceText
#	print '**',ParseList

def check_discards():
	"""
	Checks whether any of the discard phrases are in SentenceText, giving priority to the 
	+ matches. Returns [indic, match] where indic
	   0 : no matches
	   1 : simple match
	   2 : story match [+ prefix]
	"""
	global SentenceText
	
	sent = SentenceText.upper()  # case insensitive matching
	
	for target in PETRglobals.DiscardList:  # check all of the '+' cases first
		if target[0] == '+': 
			mtarg = target[1:]
			if target[-1] == '_': mtarg = mtarg[:-1]
			loc = sent.find(mtarg)
			if loc >= 0:
				if target[-1] == '_': 
					if sent[loc+len(mtarg)] in ' .!?': return [2, target]
				else: return [2, target]

	for target in PETRglobals.DiscardList:
		if target[0] != '+': 
			mtarg = target
			if target[-1] == '_': 
				mtarg = mtarg[:-1]
#				print '--',target, mtarg
			loc = sent.find(mtarg)
			if loc >= 0:
				if target[-1] == '_': 
#					print '-'+sent[loc+len(mtarg)]+'-'
					if sent[loc+len(mtarg)] in ' .!?': return [1, target]
				else: return [1, target]
	return [0,'']

def get_issues():
	"""
	Finds the issues in SentenceText, returns as a list of [code,count]
	Current version  <14.02.28> stops coding and sets the issues to zero if it finds
	*any* ignore phrase
	"""
	global SentenceText
	
	sent = SentenceText.upper()  # case insensitive matching
	issues = []
	
	for target in PETRglobals.IssueList:  
		if target[0] in sent:  # found the issue phrase
			code = PETRglobals.IssueCodes[target[1]]
			if code[0] == '~': # ignore code, so bail
				return []
			ka = 0
			gotcode = False
			while ka < len(issues):
				if code == issues[ka][0]:
					issues[ka][1] += 1
					break 
				ka += 1
			if ka == len(issues): # didn't find the code, so add it
				issues.append([code,1])	

	return issues

def code_record():
# code using ParseList read_TreeBank, then return results in StoryEventList
# first element of StoryEventList for each sentence -- this signals the start of a list 
# events for a sentence -- followed by  lists containing source/target/event triples  
	global CodedEvents
	global ParseList, ShowParseList  
	global SentenceID
	global NEmpty

	CodedEvents = []  # code triples that were produced; this is set in make_event_strings
	assign_NEcodes()
	if ShowParseList: print 'code_rec-Parselist::',ParseList

	check_verbs()
	
	if len(CodedEvents) > 0:
		StoryEventList.append([SentenceID])
		for event in CodedEvents: 
			StoryEventList.append(event)
#			print SentenceID + '\t' + event[0] + '\t' + event[1] + '\t' + event[2]
	else: 
		NEmpty += 1
		print "No events coded"
		
#	if len(raw_input("Press Enter to continue...")) > 0: sys.exit()

	
def write_events():
	"""
	Check for duplicates in the article_list, then write the records in PETR format
	<14.02.28>: Duplicate checking currently not implemented
	<14.02.28>: Currently set to code only events with identified national actors
	"""
	global StoryDate,  StorySource, SentenceID, StoryEventList, fevt
	global NEvents
	global StoryIssues
	
	if len(StoryEventList) == 0: return  
#	print "we: Mk0", StoryEventList
	for eventlist in StoryEventList: 
#		print "we: Mk1", eventlist
		if len(eventlist) == 1: # signals new sentence id
			sent_id = eventlist[0]
		else: # write the event
			if eventlist[0][0] != '-' and  eventlist[1][0] != '-':  # do not print unresolved agents
				print 'Event:',StoryDate + '\t' + eventlist[0] + '\t' + eventlist[1] + '\t' + eventlist[2] + '\t' + sent_id + '\t' + StorySource
				if PETRglobals.IssueFileName != "" and len(StoryIssues[sent_id[-2:]]) > 0: 
					print '       Issues:',StoryIssues[sent_id[-2:]]
				fevt.write(SentenceDate + '\t' + eventlist[0] + '\t' + eventlist[1] + '\t' + eventlist[2])

				if PETRglobals.IssueFileName != "":
					fevt.write('\t')
					ka = 0
					while ka < len(StoryIssues[sent_id[-2:]]):
						fevt.write(StoryIssues[sent_id[-2:]][ka][0] + ' ' + str(StoryIssues[sent_id[-2:]][ka][1]))  # output code and count
						if ka < len(StoryIssues[sent_id[-2:]]) - 1: fevt.write(', ')
						ka += 1
					
				fevt.write('\t' + sent_id + '\t' + StorySource + '\n')
				NEvents += 1
				
def make_fake_events():
# just for debugging, but you probably always guessed that
	global SentenceID,  StoryEventList
	StoryEventList.append([SentenceID])
	ka = 1
	while ka < 5:
		StoryEventList.append(['ABC','EDF',str(ka).zfill(4)])
		ka += 1
		
def do_coding():
	"""
	Main coding loop
	Note that entering any character other than 'Enter' at the prompt will stop the
	program: this is deliberate.
	<14.02.28>: Bug: PETRglobals.PauseByStory actually pauses after the first sentence of 
	            the *next* story
	"""
	global StoryDate,  StorySource, SentenceID, SentenceCat, SentenceText 
	global CurStoryID, SkipStory
	global NStory, NSent, NEvents, NDiscardSent, NDiscardStory, NEmpty, NParseErrors
	global fevt
	global StoryIssues
	global CodedEvents

	fevt = open(PETRglobals.EventFileName,'w')
	print "Writing events to:",PETRglobals.EventFileName

	NStory = 0 ; NSent = 0 ; NEvents = 0 ; NEmpty  = 0 
	NDiscardSent = 0 ; NDiscardStory  = 0 ; NParseErrors = 0 

	kfile = 0
	while kfile < len(PETRglobals.TextFileList):
		PETRreader.open_FIN(PETRglobals.TextFileList[kfile],"text")
		reset_event_list(True)
		ka = 0
		while True:
			try: read_record()
			except EOFError:
				print "Closing:",PETRglobals.TextFileList[kfile]
				PETRreader.close_FIN()
				write_events()
				break
#			print SentenceID[-6:-3],':',CurStoryID   # debug

			if not PETRglobals.CodeBySentence:
				if SentenceID[-6:-3] != CurStoryID:   # write events when we hit a new story
					if not SkipStory: write_events()
					reset_event_list()
					if PETRglobals.PauseByStory:
						if len(raw_input("Press Enter to continue...")) > 0: sys.exit()
			else: reset_event_list()
				
			if SkipStory: 
				print "Skipped"
				continue
			
			disc = check_discards()
			if disc[0] > 0:
				if disc[0] == 1: 
					print "Discard sentence:", disc[1]
					NDiscardSent += 1
				else:
					print "Discard story:", disc[1]
					SkipStory = True
					NDiscardStory += 1

			else: 
				try: code_record()
#				try: make_fake_events(); CodedEvents = ['xxx']  # debug		
				except UnbalancedTree as why:
					print "Unable to interpret parse tree:", why
					CodedEvents = []  					
						
				if len(CodedEvents) > 0 and PETRglobals.IssueFileName != "": 
					StoryIssues[SentenceID[-2:]] = get_issues()
#					print SentenceID[-2:]   # debug

			if PETRglobals.CodeBySentence:   # debug
				if not SkipStory: write_events()
				reset_event_list()
				
			if PETRglobals.PauseBySentence:
				if len(raw_input("Press Enter to continue...")) > 0: sys.exit()

			ka += 1 # debug
#			if ka > 32: break  # debug
		kfile += 1
		write_events()

	fevt.close()  # need to handle this somewhere
	print "Summary:"
	print "Stories read:",NStory,"   Sentences coded:", NSent, "  Events generated:", NEvents
	print "Discards:  Sentence", NDiscardSent, "  Story", NDiscardStory, "  Sentences without events:", NEmpty
	print "Parsing errors:", NParseErrors
			
# ================== MAIN PROGRAM ================== #		

def process_command_line():
# processes the command line arguments
# also sets a couple of run globals
	""" Command Line Options
	-v <filename>: Use the validation file <filename> 
	-c <filename>: Use the configuration file <filename> 
	-e <filename>: <filename> is the event output file
	-t <filename>: Code the single text file <filename> 
	"""
	global DoValidation
	if len(sys.argv) > 1:   # process command line options
		print "Command line options:"
	
		if ("-v" in sys.argv):
			PETRglobals.TextFileList = [sys.argv[sys.argv.index("-v")+1]]
			DoValidation = True	
			print "-v: Reading validation file from",PETRglobals.TextFileList[0]
		if ("-c" in sys.argv):
			PETRglobals.ConfigFileName  = sys.argv[sys.argv.index("-c")+1]
			print "-c: Reading configuration file from",PETRglobals.ProjectFilename
		if ("-t" in sys.argv):
			PETRglobals.TextFileList = [sys.argv[sys.argv.index("-t")+1]]
			print "-t: Reading texts from",PETRglobals.TextFileList[0]
		if ("-e" in sys.argv):
			PETRglobals.EventFileName  = sys.argv[sys.argv.index("-e")+1]
			print "-to: Writing event to ",PETRglobals.EventFileName
			
	PETRglobals.RunTimeString = time.asctime()

"""
PETRreader.read_issue_list()
#PETRreader.show_AgentDict()
sys.exit()
"""

"""
PETRreader.read_verb_dictionary('PETR.Validate.verbs.txt')
PETRreader.show_verb_dictionary()
sys.exit()
"""

process_command_line()
PETRreader.parse_Config() # debug
#sys.exit()

if DoValidation:
	open_validation_file()	
	start_time = time.time()
#	PETRreader.show_ActorDict('ActorDict.content.txt') # debug
#	sys.exit()
	PETRreader.open_FIN(PETRglobals.TextFileList[0],"validation")
	line = PETRreader.read_FIN_line() 
	while "</Environment>" not in line:  # no need to error check since open_validation_file already found this
		line = PETRreader.read_FIN_line() 
	
	while True:
		try: 
			vresult = evaluate_validation_record()	
			if vresult:
				print "Events correctly coded in",SentenceID
			else:
				print "Error: Mismatched events in",SentenceID
				sys.exit()  # debug

			if ValidPause == -1: continue  # evaluate pause conditions
			elif ValidPause == 1 or not vresult:
				inkey = raw_input("Press <Return> to continue; 'q' to quit-->")
				if 'q' in inkey or 'Q' in inkey: break

		except EOFError:
			print "Exiting: end of file"
			PETRreader.close_FIN()
			sys.exit()
		except StopCoding:
			print "Exiting: <Stop> record "
			PETRreader.close_FIN()
			sys.exit()
		except SkipRecord:
			line = PETRreader.FINline
			while '</Sentence>' not in line: line = PETRreader.read_FIN_line() 
		

else: # standard coding from the config file
	start_time = time.time()
	PETRwriter.open_ErrorFile()  # need to allow this to be set in the config file or command line
	print 'Verb dictionary:',PETRglobals.VerbFileName
	PETRreader.read_verb_dictionary()
	print 'Actor dictionaries:',PETRglobals.ActorFileList
	for actdict in PETRglobals.ActorFileList:
		PETRreader.read_actor_dictionary(actdict)
#	PETRreader.show_ActorDict('ActorDict.content.txt') # debug
	print 'Agent dictionary:',PETRglobals.AgentFileName
	PETRreader.read_agent_dictionary()
	print 'Discard dictionary:',PETRglobals.DiscardFileName
	PETRreader.read_discard_list()
	if PETRglobals.IssueFileName != "":
		print 'Issues dictionary:',PETRglobals.IssueFileName
		PETRreader.read_issue_list()
	
	do_coding()

	print "Coding time:",time.time() - start_time 
	PETRwriter.close_ErrorFile()  # note that this will be removed if there are no errors

print "Finished"


