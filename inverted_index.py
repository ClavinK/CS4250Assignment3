#-------------------------------------------------------------------------
# AUTHOR: Calvin Kamada
# FILENAME: inverted_index.py
# SPECIFICATION: Program that maintains document and inverted_index collection and demonstrates MongoDB 
# operations in Python
# FOR: CS 4250 - Assignment #3
# TIME SPENT: 3 Hours
#-------------------------------------------------------------------------

# Importing Python libraries
from pymongo import MongoClient
import string

# Connecting to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Accessing the database and collections
db = client["assignment3"]
documents = db["documents"]
inverted_index = db["inverted_index"]


#-------------------------------------------------------------------------
# FUNCTION: getTermFrequencies
# SPECIFICATION: receives a text and returns the frequency of each term
#-------------------------------------------------------------------------
def getTermFrequencies(text):

    # Converting text to lowercase
    text = text.lower()

    # Removing punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))


    # Splitting the text into terms
    terms = text.split()


    # Returning the term frequencies
    freq = {}
    for word in terms:
        if word not in freq:
            freq[word] = 0
        freq[word] += 1
    return freq

#-------------------------------------------------------------------------
# FUNCTION: addPosting
# SPECIFICATION: adds a posting to an existing term or creates a new term
#-------------------------------------------------------------------------
def addPosting(term, docId, tf):

    # Searching for the term in the inverted index
    term_document = inverted_index.find_one({
        "term": term
    })


    # Creating a new term if it does not exist
    if term_document is None:
        inverted_index.insert_one({
            "term": term,
            "postings": [
                {
                    "docId": docId,
                    "tf": tf
                }
            ]
        })
        return


    # Adding a posting if the term already exists
    for posting in term_document["postings"]:
        if posting["docId"] == docId:
            inverted_index.update_one(
                {
                    "term": term,
                    "postings.docId": docId
                },
                {
                    "$set": {
                        "postings.$.tf": tf
                    }
                }
            )
            return

    # The term exists, but does not have a posting yet
    inverted_index.update_one(
        {
            "term": term
        },
        {
            "$push": {
                "postings": {
                    "docId": docId,
                    "tf": tf
                }
            }
        }
    )



#-------------------------------------------------------------------------
# FUNCTION: removePosting
# SPECIFICATION: removes a document posting from a term and deletes the
#                term if its postings list becomes empty
#-------------------------------------------------------------------------
def removePosting(term, docId):

    # Removing the posting from the term
    inverted_index.update_one(
        {"term": term},
        {"$pull": {"postings": {"docId": docId}}}
    )

    # Retrieving the term after removing the posting
    term_document = inverted_index.find_one({
        "term": term
    })


    # Deleting the term if its postings list is empty
    if term_document is not None and len(term_document["postings"]) == 0:
        inverted_index.delete_one({
            "term": term,
            "postings": []
        })



#-------------------------------------------------------------------------
# FUNCTION: insertDocument
# SPECIFICATION: inserts a document and updates the inverted index
#-------------------------------------------------------------------------
def insertDocument(document):

    # Inserting the document into the documents collection
    documents.insert_one(document)


    # Obtaining the term frequencies
    freq = getTermFrequencies(document["text"])


    # Updating the inverted index
    for term, tf in freq.items():
        addPosting(term, document["_id"], tf)
        



#-------------------------------------------------------------------------
# FUNCTION: updateDocument
# SPECIFICATION: updates a document and makes the corresponding changes
#                to the inverted index
#-------------------------------------------------------------------------
def updateDocument(docId, newText):

    # Retrieving the current document
    curr_doc = documents.find_one({
        "_id": docId
    })

    # Obtaining the old and new term frequencies
    old_freq = getTermFrequencies(curr_doc["text"])
    new_freq = getTermFrequencies(newText)

    # Processing terms that existed in the old document
    for term in old_freq:
        if term not in new_freq:
            removePosting(term, docId)
        elif old_freq[term] != new_freq[term]:
            removePosting(term, docId)
            addPosting(term, docId, new_freq[term])

    # Processing terms that occur only in the new document
    for term in new_freq:
        if term not in old_freq:
            addPosting(term, docId, new_freq[term])
        


    # Updating the document text
    documents.update_one(
        {
            "_id": docId
        },
        {
            "$set": {
                "text": newText
            }
        }
    )



#-------------------------------------------------------------------------
# FUNCTION: deleteDocument
# SPECIFICATION: deletes a document and removes all of its postings from
#                the inverted index
#-------------------------------------------------------------------------
def deleteDocument(docId):

    # Retrieving the document before deleting it
    curr_doc = documents.find_one({
        "_id": docId
    })


    # Obtaining the terms contained in the document
    terms = getTermFrequencies(curr_doc["text"])


    # Removing the document from every corresponding posting list
    for term in terms:
        removePosting(term, docId)


    # Deleting the document
    documents.delete_one({
        "_id": docId
    })



#-------------------------------------------------------------------------
# Executing the sequence of operations
#-------------------------------------------------------------------------

# Operation 1: document 1 is obtained
document1 = {
    "_id": 1,
    "text": "Summer rain is common in Florida."
}

insertDocument(document1)


# Operation 2: document 2 is obtained
document2 = {
    "_id": 2,
    "text": "Summer is hot in Arizona."
}

insertDocument(document2)


# Operation 3: document 1 is updated
updateDocument(
    1,
    "Summer rain is hot rain in Florida."
)


# Operation 4: document 3 is obtained
document3 = {
    "_id": 3,
    "text": "Hot summer rain in California."
}

insertDocument(document3)


# Operation 5: document 2 is deleted
deleteDocument(2)

# Operation 6: print the content of the documents and inverted_index collections
for document in documents.find():
    print(document)
    
for term_document in inverted_index.find():
    print(term_document)