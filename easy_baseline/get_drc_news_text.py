"""
get the text of all disaster news of the DRC crawl
"""

import os
import json
import sys
import re
import argparse
import codecs
sys.path.append("/infolab/node4/lukuang/code/InfoChain")
from data.drc_data.news_data import DRCNews
from data.drc_data.query import DRCQuery

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dest_dir")
    parser.add_argument("--day_limit","-dl",type=int,default=60)
    args=parser.parse_args()

    drc_queries =  DRCQuery()
    count = 0
    for qid in drc_queries.queries:
        print "Generating text for disaster:%s" %(drc_queries.queries[qid])
        single_disaster_news = DRCNews(qid,args.dest_dir,args.day_limit)
        single_disaster_news.write_in_trec_format()
        count += 1
        print "There are %d queries yet to be processed" %(len(drc_queries.queries)-count)

if __name__=="__main__":
    main()

