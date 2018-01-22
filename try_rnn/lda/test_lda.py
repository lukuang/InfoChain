"""
test very simple lda on the test day
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle

import gensim
from gensim import corpora
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
import string
stop = set(stopwords.words('english'))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    # load documents
    documents = json.load(open(os.path.join(args.data_dir,"documents")))
    doc_clean = [clean(doc).split() for doc in documents] 

    # Creating the term dictionary of the corpus, where every unique term is assigned an index.
    dictionary = corpora.Dictionary(doc_clean)

    # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
    
    # Creating the object for LDA model using gensim library
    Lda = gensim.models.ldamodel.LdaModel

    # Running and Trainign LDA model on the document term matrix.
    ldamodel = Lda(doc_term_matrix, num_topics=3, id2word = dictionary, passes=50)

    # print topics
    print(ldamodel.print_topics(num_topics=3, num_words=10))
    with open(os.path.join(args.dest_dir,"model.lda"), "rb") as of:
        cPickle.dump(ldamodel, file)

if __name__=="__main__":
    main()

