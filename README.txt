# Indexer.py
This Python script when run converts a compressed json.gz file into an Inverted Index by terms.
It requires the Python libraries: json, gzip, matplotlib

# Usage
To run, in the command line or terminal, type: python Indexer.py
This script requires the compressed json.gz file be in the same directory as it and that it follow the correct format:
{
  "corpus" :
  {
    "playId" : "antony_and_cleopatra",
    "sceneId" : "antony_and_cleopatra:2.8",
    "sceneNum" : 549 ,
    "text" : "scene ix another part of the plain enter mark antony and domitiu enobarbu mark antony set we our squadron on yond side o 
              the hill in eye of caesar s battle from which place we may the number of the ship behold and so proceed accordingly 
              exeunt "
  }
}

# License
I technically have a driver's license but it has been over 10 years since I last drove.
