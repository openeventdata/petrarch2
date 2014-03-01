PETRARCH-Development
====================

Code for the stand-alone development version of PETARCH (PETR.coder.py and associated modules)

See the header of PETR_coder.py for details on the current state of the program. In a 
nutshell, this works -- it coded 60,000 AFP sentences from the GigaWord corpus without 
crashing, using the included dictionaries -- but the pattern matching is only partially 
implemented (and there are about six known potentially lethal errors that are currently 
trapped in order to avoid crashes), so effectively it is an exceedingly conservative coder.

Documentation could also use a little work (really??) but is fairly complete, though 
scattered in """...""" blocks throughout the program.

Due to constraints on time, this has not been retrofitted into the structure found in 
the "PETRARCH" repo: we will eventually do this.

The PETR_config.ini file is configured to code the file GigaWord.sample.PETR.txt, which is 
an exceedingly tiny sample of the LDC Gigaword corpus file afp_eng_200808.xml formatted  
into PETR format using the program LDCGW.PETR.format.py, which is also included in the repo.

