import json
import gzip
import matplotlib.pyplot as plt


####################################################################################################################################

# Postings have a document ID and a list of positions where the associated term appears in said document
class Posting:
    def __init__(self, d, p):
        self.docId = d # ID of the document
        self.positions = [p] # Indices in the document where the term appears. Cannot be empty. Defaults with one.

    def add(self, p): # Add an index to the list of positions
        self.positions.append(p)
    
    def getDocId(self): # Accessor to return docId
        return self.docId

    def getPositions(self): # Accessor to return positions list
        return self.positions
    
####################################################################################################################################

# PostingList has
    # postings: a list of Posting objects
        # Cannot be empty. Is constructed with a Posting already added
    # current: an index of the Posting being currently looked at
    # last: an index of the last Posting to be added to postings

class PostingList:
    def __init__(self, d, p): # Constructor requires a document ID and a position
        self.postings = [Posting(d, p)] # Cannot make an empty PostingList. Defaults with one added.
        self.current = 0 # Index for current Posting
        self.last = 0 # Index for last added Posting
    
    def add(self, d, p):
        if self.postings[self.last].getDocId() == d: # If the docId of the most recently added Posting is the same as d
            self.postings[self.last].add(p) # Add the position p to the current Posting
        else:
            self.postings.append(Posting(d, p)) # Otherwise, append a new Posting to the list with docId d and position p.
            self.last += 1 # Increment index of last added Posting
    
    def getPostings(self): # Accessor for postings list
        return self.postings

    def getCurrentDoc(self): # Accessor for current document ID
        return self.postings[self.current].getDocId()
    
    def getCurrentPositions(self): # Accessor for positions of current Posting
        return self.postings[self.current].getPositions()
    
    def hasMore(self): # Checks if current is still less than the last index available
        if self.current < len(self.postings) - 1:
            return True # If it is still not at the last index, return True
        return False
    
    def skipTo(self, d): # Modifies value of current to index of a document with ID >= to d
        self.current = 0
        while self.getCurrentDoc() < d and self.hasMore():
            self.current += 1
        """
        while self.postings[self.current].getDocId() > d and self.current > 0: # If called when already past d
            self.current -= 1 # Keep decrementing
        while self.postings[self.current].getDocId() < d and self.hasMore(): # While the document ID is still less than d
            self.movePast() # Keep incrementing
        """
    
    def movePast(self): # Modifies value of current
        self.current += 1 # Just increments once

####################################################################################################################################

# MAIN
# Index creation starts here

####################################################################################################################################

jsonfilename = "shakespeare-scenes.json.gz" # File name

index = dict() # Base form of the index is a dictionary
meta = [] # List for metadata entries

with gzip.open(jsonfilename, "r") as f: # Open compressed file

    dataset = json.loads(f.read().decode('utf-8')) # Read file as json data with utf-8 encoding
    documents = dataset['corpus'] # dictionary dataset at key 'corpus' contains the actual documents as a list of dictionaries
    docCount = len(documents) # How many documents there are

    # For all documents
    for d in range(0, docCount):
        # Dictionary at index d
        doc = documents[d]

        # Pulling out features of doc
        playId = doc['playId']
        sceneId = doc['sceneId']
        sceneNum = doc['sceneNum']

        # Append a new object containing the three features other than 'text' as metadata
        meta.append({ 'playId':playId, 'sceneId':sceneId, 'sceneNum':sceneNum })

        # Pull out actual content of the doc
        text = doc['text']
        words = text.split()
        wordCount = len(words)

        # For every word in the document
        for p in range(0, wordCount):
            w = words[p]

            # If the word has not been added to the inverted index
            if w not in index.keys():
                # Add it as a new key with a new PostingList as the value
                index[w] = PostingList(d, p)
            else:
                # Otherwise, add the position to the current Posting
                index[w].add(d, p)

# Index creation ends here

####################################################################################################################################


# Functions


####################################################################################################################################

# Function for Terms0

####################################################################################################################################
# Function designed for producing terms0.txt's content
# Takes two lists of postings and two terms.
# The postings1 and term1 are the list of postings and term that you want to have more frequency per document.

"""
NOTE
I wrote this before implementing Document At A Time Retrieval for Conjunctive Processing. So this is a very long function that does too much work on its own.
To improve this, I'd use my Conjunctive Processing function to get all the documents where "Thee" and "You" occur
Then I'd write a function to check for all those documents which ones had the larger len(positions) for "Thee". Then repeat for "Thou" vs "You".
"""
def terms_0(postings1, postings2):
    first = 0 # Indices to keep track of how far we are in each posting list
    second = 0

    docIds = set() # Set to hold docIds where frequency of term1 > frequency of term2 in current document

    while first < len(postings1) and second < len(postings2): # While both posting lists still have more postings to consider
        d1 = postings1[first].getDocId()
        d2 = postings2[second].getDocId()
    
        if d1 == d2: # If the docIds match, then we're looking at the same document
            len1 = len(postings1[first].positions)
            len2 = len(postings2[second].positions)

            if len1 > len2: # If term1 is more frequent than term2 in current document
                docIds.add(d1) # Add it to the set of docIds

            first += 1 # We are done with the current index for both posting lists.
            second += 1 # Increment both

        elif d1 < d2:
            first += 1 # If docId of term1 is lower, increment it
        elif d1 > d2:
            second += 1 # Or if docId of term2 is lower, increment it
    
    return docIds # Return set of docIds for scenes where term1 is more frequent than term2

####################################################################################################################################

# Non-conjunctive Processing

####################################################################################################################################

# Returns set of all docIds from a list of postings
# Non-conjunctive processing for document IDs of all documents containing any of the terms
def getAllDocIds(terms, index):
    docIds = set()

    for t in terms: # For every term
        posting = index[t].getPostings() # Get the postings
        for p in posting: # For each posting
            docIds.add(p.getDocId()) # Get the document ID and add it to the set

    return docIds # Return the set of document IDs

####################################################################################################################################

# Document At A Time Retrieval Conjunctive Processing Function
# Based on pseudocode on p. 174 in textbook

####################################################################################################################################

# Q is the query, I is the index
def daatRetrieval(Q, I):
    L = [] # List of inverted lists
    D = set() # Documents set where all terms of query appear

    if len(Q) == 0:         # If empty query:
        return D                # Return empty set D;

    for q in Q:             # For each term in the query Q:
        L.append(I[q])          # Add the inverted list to L;
    
    d = -1 # Initialize d to -1 meaning not all terms appear in the current document

    done = False
    while not done: # While there are still elements in the lists to check:
        for l in L: # For each inverted list:
            if l.getCurrentDoc() > d: # If the current document is greater:
                d = l.getCurrentDoc() # Set that as the earliest document candidate d;

        for l in L: # For each inverted list:
            l.skipTo(d) # Skip them to the candidate document;

            if l.getCurrentDoc() == d: # If the term appears in this document:
                l.movePast() # Move on;
            else: # Otherwise if the term does not appear in document d:
                d = -1 # Set to -1 to indicate that this document is no longer a candidate;

            if not l.hasMore(): # If the list does not have more to check:
                done = True # Set done to True and the while loop will end;

        if d > -1: # If the document d is not -1:
            D.add(d) # d is a document where all terms appear. Add them to the set;

    return D # Return set D of documents where all terms in Q appear;

####################################################################################################################################

# Phrase finding function
# query is a list of terms that make up the query (in order).
# document is the docId of the document where all terms are guaranteed to appear(obtained by running daatRetrieval(Q, I)).
# current is the index of the second of the two terms being compared. Increments with each recursion (defaults to the second term)

def findPhrase(query, index, docId, current = 1, first = 0):

    if len(query) <= 1: # If only looking at 1 or less terms, then the list of documents where it appears at all is the result
        return daatRetrieval(query, index)

    term1 = query[current - 1] # Terms being compared (current is the index in query of second term)
    term2 = query[current]

    invertedList1 = index[term1] # Reference to inverted lists
    invertedList2 = index[term2]
    
    invertedList1.skipTo(docId) # Skip both inverted lists to document (docId of the document where all terms of the query appear)
    invertedList2.skipTo(docId)
    
    positions1 = invertedList1.getCurrentPositions() # After skipping to the desired document, get the positions lists for both terms in the document
    positions2 = invertedList2.getCurrentPositions()

    # Index being looked second terms' positions lists.
    second = 0

    match = False # Default to no match
    while first < len(positions1) and second < len(positions2): # While there are more positions to check in both lists
        if positions1[first] + 1 == positions2[second]: # If the first term appears right before the second
            if current == len(query) - 1: # If this is the last term in the query
                return True # Return True to previous recursion calls
            else: # Otherwise, if there are more terms to check, 
                match = findPhrase(query, index, docId, current + 1, second)
            
            if match:
                return match # Return True if match found
            # If no return yet, increment indices to check next positions
            first += 1
            second += 1
        # If value in positions1 at first < value in positions2 at second
        elif positions1[first] + 1 < positions2[second]:
            first += 1 # Increment first index
        # If reversed
        elif positions1[first] + 1 > positions2[second]:
            second += 1 # Increment second index
                             
    return match

# End of functions

####################################################################################################################################


# Query handling starts here


####################################################################################################################################
# Terms 0: Scenes where 'thee' and 'thou' > 'you'

# Postings for the three terms
pThee = index['thee'].postings
pThou = index['thou'].postings
pYou = index['you'].postings

docIds0 = terms_0(pThee, pYou) # Function call to terms_0 returns set of docIds where term1('thee') is more frequent than term2('you')
docIds0.update(terms_0(pThou, pYou)) # Add the call on 'thou' as term1 to the result set

terms_scenes0 = set()
for d in docIds0:
    terms_scenes0.add(meta[d]['sceneId'])

# File writing
terms_file0 = open("terms0.txt", "w")

# Sorting
scenes = []
for s in terms_scenes0:
    scenes.append(s)
sorted_scenes = sorted(scenes)

terms_file0.write("Terms 0: Scenes where \"thou\" or \"thee\" are used more than \"you\"\n")
for s in sorted_scenes:
    terms_file0.writelines(s + '\n')

terms_file0.close()

####################################################################################################################################
# Terms 1: Scenes w/ 'verona', 'rome', or 'italy'

# All documents where the term(s) appear (non-conjunctive)
terms1 = ['verona', 'rome', 'italy']
docIds1 = getAllDocIds(terms1, index)

# All scenes of the documents found
terms_scenes1 = set()
for d in docIds1:
    terms_scenes1.add(meta[d]['sceneId'])

# Sorting
scenes = []
for s in terms_scenes1:
    scenes.append(s)
sorted_scenes = sorted(scenes)

# File writing
terms_file1 = open("terms1.txt", "w")

terms_file1.write("Terms 1: Scenes where \"verona\", \"rome\", or \"italy\" are mentioned\n")
for s in sorted_scenes:
    terms_file1.write(s + '\n')

terms_file1.close()

####################################################################################################################################
# Terms 2: Plays w/ 'falstaff'

# All documents where the term(s) appear (non-conjunctive)
terms2 = ['falstaff']
docIds2 = getAllDocIds(terms2, index)

# All plays where the term appears
terms_plays2 = set()
for d in docIds2:
    terms_plays2.add(meta[d]['playId'])

# Sorting
plays = []
for p in terms_plays2:
    plays.append(p)
sorted_plays = sorted(plays)

# File writing
terms_file2 = open("terms2.txt", "w")
terms_file2.write("Terms 2: Plays where \"falstaff\" is mentioned\n")
for p in sorted_plays:
    terms_file2.write(p + '\n')

terms_file2.close()

####################################################################################################################################
# Terms 3: Plays w/ 'soldier'

# All documents where the term(s) appear (non-conjunctive)
terms3 = ['soldier']
docIds3 = getAllDocIds(terms3, index)

# All plays where the term appears
terms_plays3 = set()
for d in docIds3:
    terms_plays3.add(meta[d]['playId'])

# Sorting
plays = []
for p in terms_plays3:
    plays.append(p)
sorted_plays = sorted(plays)

# File writing
terms_file3 = open("terms3.txt", "w")

terms_file3.write("Terms 3: Plays where \'soldier\' is mentioned\n")
for p in sorted_plays:
    terms_file3.write(p + '\n')

terms_file3.close()

####################################################################################################################################
# Phrase 0: "Lady MacBeth"

# All documents where all terms appear
phrase0 = ['lady', 'macbeth']
shared_docs0 = daatRetrieval(phrase0, index)

# All scenes where the phrase appears (conjunctive)
phrase_scenes0 = set()
for d in shared_docs0:
    if findPhrase(phrase0, index, d):
        phrase_scenes0.add(meta[d]['sceneId'])

# Sorting
scenes = []
for s in phrase_scenes0:
    scenes.append(s)
sorted_scenes = sorted(scenes)

# File writing
phrase0_file = open("phrase0.txt", "w")

phrase0_file.write("Phrase 0: Scenes where \"Lady MacBeth\" is mentioned:\n")
for s in sorted_scenes:
    phrase0_file.write(s + '\n')

phrase0_file.close()

####################################################################################################################################
# Phrase 1: "A rose by any other name"

# All documents where all terms appear
phrase1 = ['a', 'rose', 'by', 'any', 'other', 'name']
shared_docs1 = daatRetrieval(phrase1, index)

# All scenes where the phrase appears (conjunctive)
phrase_scenes1 = set()
for d in shared_docs1:
    if findPhrase(phrase1, index, d):
        phrase_scenes1.add(meta[d]['sceneId'])

# Sorting
scenes = []
for s in phrase_scenes1:
    scenes.append(s)
sorted_scenes = sorted(scenes)

# File writing
phrase1_file = open("phrase1.txt", "w")

phrase1_file.write("Phrase 1: Scenes where \"A rose by any other name\" is mentioned:\n")
for s in sorted_scenes:
    phrase1_file.write(s + '\n')

phrase1_file.close()

####################################################################################################################################
# Phrase 2: "Cry havoc"

# All documents where all terms appear
phrase2 = ['cry', 'havoc']
shared_docs2 = daatRetrieval(phrase2, index)

# All scenes where the phrase appears (conjunctive)
phrase_scenes2 = set()
for d in shared_docs2:
    if findPhrase(phrase2, index, d):
        phrase_scenes2.add(meta[d]['sceneId'])

# Sorting
scenes = []
for s in phrase_scenes2:
    scenes.append(s)
sorted_scenes = sorted(scenes)

# File writing
phrase2_file = open("phrase2.txt", "w")

phrase2_file.write("Phrase 2: Scenes where \"Cry havoc\" is mentioned:\n")
for s in sorted_scenes:
    phrase2_file.write(s + '\n')

phrase2_file.close()

####################################################################################################################################


# Graph plotting


####################################################################################################################################

theeyou_docs = daatRetrieval(['thee', 'you'], index)

thee_x = []
thee_y = []
you_y1 = []

for d in theeyou_docs:
    index['thee'].skipTo(d)
    index['you'].skipTo(d)

    thee_x.append(meta[d]['sceneNum'])
    thee_y.append(len(index['thee'].getCurrentPositions()))
    you_y1.append(len(index['you'].getCurrentPositions()))

thouyou_docs = daatRetrieval(['thou', 'you'], index)

thou_x = []
thou_y = []
you_y2 = []

you_x = thee_x
for i in thou_x:
    you_x.append(i)

you_y = you_y1
for i in you_y2:
    you_y.append(you_y2)

for d in thouyou_docs:
    index['thou'].skipTo(d)
    index['you'].skipTo(d)

    thou_x.append(meta[d]['sceneNum'])
    thou_y.append(len(index['thou'].getCurrentPositions()))
    you_y2.append(len(index['you'].getCurrentPositions()))


fig = plt.Figure()
plt.suptitle("\"Thee\" or \"Thou\" vs \"You\" Word Count Over Scene Num")
plt.xlabel("SceneNum")
plt.ylabel("Word count")
plt.plot(thee_x, thee_y, label = "\"thee\" counts", color = 'red')
plt.plot(thou_x, thou_y, label = "\"thou\" counts", color = 'blue')
plt.plot(you_x, you_y, label = "\"you\" counts", color = 'green')
plt.legend(loc = "upper left")
plt.show()

####################################################################################################################################


# END


####################################################################################################################################
