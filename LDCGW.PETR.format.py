##	LDCGW.PETR.format.py
##
##  This program reformats the LDC 'Gigaword' XML (parsed) files into PETARCH format; it
##  is used to generate a set of test sentences. Various caveats
##  
##  1. Files contain approximately SentLimit sentences each, though the files are broken
##     at story boundaries
##
##  2. Only the first SeqLimit sentences in each story are processed.
##
##  3. Sentences beginning or ending with `,', or ", i.e direct quotes, are skipped
##
##  4. Sentences with fewer than WordLimit are skipped: this gets rid of a lot of sports
##     and financial reports
##
##	TO RUN PROGRAM:
##
##	python LDCGW.PETR.format.py <input file> <output prefix>
##
##	PROGRAMMING NOTES: 
##
##  1. Only limited robustness checking; files seem pretty reliably standardized so far.
##
##  2. This is currently producing only a 1-digit sentence number, whereas PETR expects
##     two-digits. As of 14.02.28, the development version of PETR adjusts for this.
##     Obviously it would be better to make the adjustment here, and not in PETR. An 
##     issue for the next coding binge.
##
##  3. It would be useful to add a new <Source id="..."> line to list the file.      
##
##	SYSTEM REQUIREMENTS
##	This program has been successfully run under Mac OS 10.6; it is standard Python 2.5
##	so it should also run in Unix or Windows. 
##
##	PROVENANCE:
##	Programmer: Philip A. Schrodt
##				Parus Analytical Systems
##				http://eventdata.parusanalytics.com
##
##	Copyright (c) 2014	Philip A. Schrodt.	All rights reserved.
##
## This project was funded in part by National Science Foundation grant 
## SES-1004414
##
##	Redistribution and use in source and binary forms, with or without modification,
##	are permitted under the terms of the GNU General Public License:
##	http://www.opensource.org/licenses/gpl-license.html
##
##	Report bugs to: schrodt735@gmail.com
##
##	REVISION HISTORY:
##	12-Jan-14:	Initial version
##
##	----------------------------------------------------------------------------------

import sys

monthstr = 'JanFebMarAprMayJunJulAugSepOctNovDec'
SentLimit = 5000  # number of sentences per file
SeqLimit = 6 # max number of sentences extracted per story
WordLimit = 24  # minimum number of words for a sentence

# ============ main program =============== #

if len(sys.argv) > 1: textfile = sys.argv[1]
else:  textfile = 'Textfiles.list'

if len(sys.argv) > 2: prefix = sys.argv[2]
else: prefix = 'TEST00'

try: 
	fin = open(textfile,'r')
except IOError:
	print "\aError: Could not find the input file"
	sys.exit()	

#print str(3).zfill(2)
#sys.exit()

fileno = 1  # number of files generated so far
sentno = 0  # count of sentences in file
storyno = 0 # sequence of sentence in story

fout = open(prefix+'-01.txt','w')
line = fin.readline() 
while len(line) > 0:  # loop through the file
	if '<DATELINE>' in line:  # note: various Python date utilities can do this more easily
		parse = fin.readline() 
		base = parse.find('(CD')  # extract the date, hoping that the format is standardized...
		par = parse.rfind(')',0,base)
		mon = parse[parse.rfind(' ',0,par-1)+1: par]
		if mon in monthstr:
			ser = monthstr.find(mon)
#			ser1 = math.floor(ser/3)+1
			ser1 = (ser/3)+1

			if ser1 < 10: monind = '0'+str(ser1)
			else: monind = str(ser1)
		else: monind = '01'   # default to this
		
		par = parse.find(')',base)
		day = parse[parse.rfind(' ',0,par-1)+1: par]
		if len(day) == 1: day = '0'+day
		
		base = parse.find('(CD',base+3)
		par = parse.find(')',base)
		year = parse[parse.rfind(' ',0,par-1)+1: par]
		
		datestr = year+monind+day
		seqno = 0   # sentence number within stories
		if sentno > SentLimit:  # check whether file is full; only break files on new stories
			fout.close()
			fileno +=1
			fout = open(prefix + '-' + str(fileno).zfill(2) + '.txt','w')
			print "New file:",fileno
			storyno = 0
			sentno = 0
		storyno += 1
#		if storyno > 64: break   # debug
		print day,mon,year,':',datestr
		
	if '<P>' in line:  
		parse = fin.readline()  # this is a parsed sentence
		seqno += 1
		if seqno > SeqLimit: 
			line = fin.readline()  
			continue
		idstr = prefix+'-'+str(fileno).zfill(2)+'-'+str(storyno).zfill(4)+'-'+str(seqno)  # this is the id string for the record

		outstr = ""  # extract the sentence text
		ka = 0
		nwords = 0    # approximate word count
		while ka < len(parse):
			par = parse.find(')',ka)
			if par < 0: break
			if parse[par-1] != ')':
				word = parse[parse.rfind(' ',0,par-1): par]
				if word[1].isalpha() or word[1].isdigit(): 
					outstr += word
					nwords += 1
				elif '-LRB-' in word: outstr += ' ['   # convert brackets
				elif '-RRB-' in word: outstr += ']'
				else: outstr += word[1:]  # other punctuation
				ka = par+1
			else: ka += 1
				
		outstr = outstr.strip()
		if nwords < WordLimit or outstr.startswith('`') or outstr.startswith('"') or outstr.startswith("'") or outstr.endswith('`') or outstr.endswith('"') or outstr.endswith("'") : # skip direct quotes
			if nwords < WordLimit : print "Skip: short"
			else: print "Skip:",outstr[0]
			line = fin.readline()  
			continue
		
		sentno += 1  # it's okay, so write a PETR record
		print outstr[:64]
		fout.write('<Sentence date = \"' + datestr + '\" id =\"' + idstr +'\">\n<Text>\n') # print the header
		ka = 0    # split text on spaces into lines < 80 chars
		kend = 80
		while kend < len(outstr):
			kend = outstr.rfind(' ',ka,kend)
#			print outstr[ka:kend]
			fout.write(outstr[ka:kend]+' \n')
			ka = kend+1
			kend += 80
#		print outstr[ka:]		
		fout.write(outstr[ka:kend]+' \n</Text>\n<Parse>\n')
			
		outstr = "" # sort of format the parse
		ka = 0
		while ka < len(parse):
			if parse.startswith('(NP (NP ',ka):
				outstr += '\n(NP (NP '
				ka += 8
			elif parse.startswith('(NP ',ka):
				outstr += '\n(NP '
				ka += 4				
			elif parse.startswith('(VP ',ka):
				outstr += '\n(VP '
				ka += 4
			elif parse.startswith('(PP ',ka):
				outstr += '\n(PP '
				ka += 4
			else:	
				outstr += parse[ka]
				ka += 1
				
#		print outstr
		fout.write(outstr+'</Parse>\n</Sentence>\n\n')

	line = fin.readline()  

fin.close()
fout.close()
print "Finished"
