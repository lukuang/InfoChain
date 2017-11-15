"""
handle queries for data crawled before DRC
"""

import os
import json
import sys
import re
import argparse
import codecs
from collections import Counter

PATH_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),"path.json")

class PreDRCQuery(object):
    def __init__(self,query_path=None):
        if query_path:
            self._query_path = query_path
        else:
            path_data = json.load(open(PATH_FILE))
            self._query_path = path_data["query"]

        self._queries = json.load(open(self._query_path))
        


    @property
    def queries(self):
        return self._queries

    def count_top_disaster(self,top=5):
        words = {}
        for qid in self._queries:
            for w in re.findall("\w+",self._queries[qid]):
                if w not in words:
                    words[w] = 0
                words[w] += 1

        c = Counter(words)
        print c.most_common(top)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()

if __name__=="__main__":
    main()

