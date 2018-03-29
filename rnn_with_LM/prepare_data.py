# encoding: utf-8
"""
prepare data
"""

import os
import json
import sys
reload(sys)  
sys.setdefaultencoding('utf8')
import re
import argparse
import codecs
import string
from random import shuffle
from nltk.tokenize import sent_tokenize

def add_space(match_obj):
    return " %s " %(match_obj.group(1))

def parse_trec_doc(doc_path,doc_count):
    doc_string = ""
    with codecs.open(doc_path, "r","utf-8") as f:
        doc_string =  f.read()

    sentences = []
    for doc_text in re.findall("<TEXT>(.+?)</TEXT>", doc_string,flags=re.DOTALL):
        doc_text = re.sub("([%s])" %(string.punctuation),add_space,doc_text)
        sentences += sent_tokenize( re.sub("\s+"," ",doc_text))
        doc_count -= 1
        if doc_count == 0:
            break
    print "\tThere are %d sentences" %(len(sentences))
    return sentences, doc_count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_path")
    parser.add_argument("dest_path")
    parser.add_argument("-ndocs",'--number-of-docs',type=int,default=1000,
        help="number of docs used for generating the data")
    parser.add_argument("-ndays",'--number-of-days',type=int)
    parser.add_argument("-r","--random",action="store_true",
        help="whether the text would be generated in random")
    parser.add_argument("--format",type=int,choices=[0,1],default=0,
        help="""
        choices of the format:
        0: for lda (raw list stored in json)
        1: for rnn (split in training, cross-valiadation, testing)
        """)
    parser.add_argument("--qids",nargs="*",default=["1","10","27"])


    args=parser.parse_args()

    sentences = []
    for qid in os.walk(args.src_path).next()[1]:
        doc_count = args.number_of_docs
        if args.qids:
            if qid not in args.qids:
                continue
        print "process qid: %s" %(qid)

        dir_path = os.path.join(args.src_path,qid)
        if args.number_of_days:
            for day in sorted(os.walk(dir_path).next()[2])[:args.number_of_days]:
                day_file = os.path.join(dir_path,day)
                print "\tprocess file %s" %(day_file)
                new_sentences,doc_count = parse_trec_doc(day_file,10000)
                sentences += new_sentences
        else:
            for day in sorted(os.walk(dir_path).next()[2]):
                day_file = os.path.join(dir_path,day)
                print "\tprocess file %s" %(day_file)
                new_sentences,doc_count = parse_trec_doc(day_file,doc_count)
                sentences += new_sentences
                print "\t%d documents left" %(doc_count)
                if doc_count == 0:
                    break

    if args.random:
        print "Shuffle Sentences"
        shuffle(sentences)

    if args.format == 0:
        dest_file = os.path.join(args.dest_path,"sentences")
        with codecs.open(dest_file, "w","utf-8") as of:
            of.write(json.dumps(sentences))
    else:
        train_file = os.path.join(args.dest_path,"train.txt")
        test_file = os.path.join(args.dest_path,"test.txt")
        valid_file = os.path.join(args.dest_path,"valid.txt")

        with open(train_file,"w") as train_f:
            train_f.write( "\n".join(sentences[:int(0.8*len(sentences))])+"\n" )


        with open(test_file,"w") as test_f:
            test_f.write( "\n".join(sentences[int(0.8*len(sentences)) : int(0.9*len(sentences))]) +"\n")

        with open(valid_file,"w") as valid_f:
            valid_f.write( "\n".join(sentences[int(0.9*len(sentences)) : ]) +"\n")





if __name__=="__main__":
    main()

