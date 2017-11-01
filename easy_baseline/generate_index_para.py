"""
generate Indri index parameter file for DRC data
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.misc import gene_indri_index_para_file

def get_corpora(data_path):

    corpora_list = []
    for qid in os.walk(data_path).next()[1]:
        corpora_list.append(os.path.join(data_path,qid))
    return corpora_list

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index_path")
    parser.add_argument("data_path")
    parser.add_argument("para_file_path")
    args=parser.parse_args()

    args.data_path = os.path.realpath(args.data_path)
    args.index_path = os.path.realpath(args.index_path)
    
    corpora_list = get_corpora(args.data_path)
    gene_indri_index_para_file(corpora_list,args.para_file_path,
                               args.index_path,use_stopper=True)


if __name__=="__main__":
    main()

