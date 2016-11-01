  ---
  title: 'PETRARCH2: Another Event Coding Program'
  tags:
    - event coding
    - natural language processing
    - computational linguistics
  authors:
   - name: Clayton Norris
     orcid: 0000-0001-5907-757X
     affiliation: 1
   - name: Philip Schrodt
     orcid: 0000-0003-3495-4198
     affiliation: 2
   - name: John Beieler
     orcid: 0000-0001-7811-4399
     affiliation: 3
  affiliations:
   - name: University of Chicago
     index: 1
   - name: Parus Analytics
     index: 2
   - name: Human Language Technology Center of Excellence<br />Johns Hopkins University
     index: 3
  date: 1 November 2016
  bibliography: paper.bib
  ---

  # Summary

  The PETRARCH2 coding program implements a new coding algorithm, based on a
  syntactic constituency parse, to extract who-did-what-to-whom political event data from
  structured news stories. Events are coded according to the CAMEO [@cameo] coding
  ontology. This software improves upon previous-generation coding software
  such as TABARI [@tabari] by using a deep syntactic parse rather than shallow 
  parsing.

  At the level of assigning codes, PETRARCH2 is largely dictionary based, working from extensive 
  dictionaries of verb phrases to identify the type of event, and noun phrases to
  identify both the actor (generally a proper noun such as the name of a country or
  leader) and agent (generally a common noun identifying a role such as "police" or
  "protesters"). These dictionaries incorporate the synonym sets from WordNet, are
  open source, and are included in the distribution.

  PETRARCH2 has primarily been run using Treebank output from the Stanford CoreNLP
  system. It can be integrated with other software on the https://github.com/openeventdata/ site
  to handle either continuous near-real-time coding or batch coding, as well as 
  auxiliary programs for geolocation and simple deduplication. 

  # References
