"""
prepare data
"""

import os
import json
import sys
import re
import argparse
import codecs
from random import shuffle


def parse_trec_doc(doc_path):
    doc_string = ""
    with open(doc_path, "r") as f:
        doc_string =  f.read()

    documents = []
    for doc_text in re.findall("<TEXT>(.+?)</TEXT>", doc_string,flags=re.DOTALL):
        documents.append( re.sub("\s+"," ",doc_text))
    print "\tThere are %d documents" %(len(documents))
    return documents

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_path")
    parser.add_argument("dest_path")
    parser.add_argument("-n",'--number-of-days',type=int,default=1,
        help="number of days used for generating the data")
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

    documents = []
    for qid in os.walk(args.src_path).next()[1]:
        if args.qids:
            if qid not in args.qids:
                continue
        print "process qid: %s" %(qid)

        dir_path = os.path.join(args.src_path,qid)
        for day in sorted(os.walk(dir_path).next()[2])[:args.number_of_days]:
            day_file = os.path.join(dir_path,day)
            print "\tprocess file %s" %(day_file)
            documents += parse_trec_doc(day_file)

    if args.random:
        shuffle(documents)

    if args.format == 0:
        dest_file = os.path.join(args.dest_path,"documents")
        with open(dest_file, "w") as of:
            of.write(json.dumps(documents))
    else:
        train_file = os.path.join(args.dest_path,"train.txt")
        test_file = os.path.join(args.dest_path,"test.txt")
        valid_file = os.path.join(args.dest_path,"valid.txt")

        with open(train_file,"w") as train_f:
            train_f.write( " ".join(documents[:int(0.8*len(documents))])+"\n" )


        with open(test_file,"w") as test_f:
            test_f.write( " ".join(documents[int(0.8*len(documents)) : int(0.9*len(documents))]) +"\n")

        with open(valid_file,"w") as valid_f:
            valid_f.write( " ".join(documents[int(0.9*len(documents)) : ]) +"\n")





if __name__=="__main__":
    main()

