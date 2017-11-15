"""
view how the entity is used for a query
"""

import os
import json
import sys
import re
import argparse
import codecs



class EntityViewer(object):
    def __init__(self,disaster_vector_result_file,index_dir):
        self._result = json.load(open(disaster_vector_result_file))
        self._index_dir = index_dir

    def show_all(self,entity):
        try:
            entity_data = self._result[entity]
        except KeyError:
            print "No entity %s found !" %(entity) 
        else:
            for temp_qid in entity_data:
                print "for %s:" %(temp_qid)
                for did in entity_data[temp_qid]:
                    self.fe(entity,did)
                print "-"*20
                
    def fe(self,entity,docid):
        os.system('dumpindex %s dt `dumpindex %s di docno %s` | grep  -E -o ".{0,100}%s.{0,100}" ' %(self._index_dir,self._index_dir,docid,entity))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disaster_vector_result_file")
    parser.add_argument("entity")
    parser.add_argument("--index_dir","-ind",default="/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/news/index")
    args=parser.parse_args()

    viewer = EntityViewer(args.disaster_vector_result_file,args.index_dir)
    viewer.show_all(args.entity)

if __name__=="__main__":
    main()

