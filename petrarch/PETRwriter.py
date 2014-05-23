##	PETRwriter.py [module]
##
# Output routines for the PETRARCH event coder
##
# CODE REPOSITORY: https://github.com/eventdata/PETRARCH
##
# SYSTEM REQUIREMENTS
# This program has been successfully run under Mac OS 10.6; it is standard Python 2.5
# so it should also run in Unix or Windows.
##
# PROVENANCE:
# Programmer: Philip A. Schrodt
# Parus Analytical Systems
# State College, PA, 16801 U.S.A.
# http://eventdata.parusanalytics.com
##
# Copyright (c) 2013	Philip A. Schrodt.
##
# This project was funded in part by National Science Foundation grant SES-1259190
##
# This code is covered under the MIT license as asserted in the file PETR.coder.py
##
# Report bugs to: schrodt735@gmail.com
##
# REVISION HISTORY:
# 22-Nov-2013:	Initial version
# ------------------------------------------------------------------------


# ============================== ERRORFILE UTILITIES ============================== #

"""
ErrorFile
The file handle ErrorFile is used to write a log of any errors encountered during
the run. The name of the file can be set with the command
	<ErrorFile name = "<file name.txt>" [unique ="true"]>
if the 'unique' option is used, a YYYYMMDDHHMM tag is added to the name prior to
a three-char .suffix  such as '.txt' (which, obviously, is required in this instance.
Otherwise the file name defaults to ErrorLog.PETR.txt.
The global ErrorN records the number errors: if this is zero at the end of the run,
the file is deleted.
"""
import time
import os
import PETRreader
import PETRglobals


def open_ErrorFile(sname='', isunique=''):
    global ErrorFile, ErrorN, ErrorfileName
    ErrorN = 0  # number of errors written to ErrorFile
    if len(sname) == 0:  # default
        ErrorfileName = 'ErrorLog.PETR.txt'
    else:
        if len(isunique) > 0:
            ErrorfileName = sname[:-3] + \
                time.strftime("%y%m%d%H%M", time.localtime()) + '.txt'
        else:
            ErrorfileName = sname
    ErrorFile = open(ErrorfileName, 'w')
#	print '--Opening',ErrorfileName
    ErrorFile.write('PETRARCH Error Log\n')
    ErrorFile.write('Run time: ' + PETRglobals.RunTimeString + '\n')


def close_ErrorFile():
# close ErrorFile and delete the file if no errors were written
    global ErrorFile, ErrorN, ErrorfileName
    ErrorFile.close()
#	print '--Closing',ErrorfileName," with",ErrorN," errors"
    if ErrorN == 0:
        os.remove(ErrorfileName)


def write_ErrorFile(str):
# writes to ErrorFile without incrementing ErrorN
    global ErrorFile
    ErrorFile.write(str)


def write_FIN_error(errorstring):
    """ Writes to ErrorFile errors that occur in input read using open_FIN and
    read_FIN_line() :
                    errorstring -- which should provide an explanation of the error
                    current file name
                    line number in the file (integer)
                    line which causes the error
    Assumes that ErrorFile is open
    errorstring only is also written to STDOUT
    This function uses the FIN functions to keep track of the line content and location
    """
    global ErrorFile, ErrorN

    ErrorN += 1
    ErrorFile.write("\n" + errorstring + "\n")
    ErrorFile.write(PETRreader.FINline)
    ErrorFile.write("Location: file " + PETRreader.CurrentFINname +
                    ", line " + str(PETRreader.FINnline) + "\n")
    print errorstring


def write_record_error(errorstring, recordid='', recordcat=''):
    """ Writes to ErrorFile from functions that are processing records
                    errorstring -- which should provide an explanation of the error
                    recordid -- usually SentenceID; if null, second write is not executed
                    recordcat -- usually SentenceCat
    Assumes that ErrorFile is open
    """
    global ErrorFile, ErrorN

    ErrorN += 1
    ErrorFile.write("\n" + errorstring + ":")
    print errorstring,
    if len(recordid) > 0:
        ErrorFile.write("Record " + recordid)
        print ':', recordid,
        if len(recordcat) > 0:
            ErrorFile.write(' [' + recordcat + ']')
            print '[', recordcat, ']',
    print '\n',
