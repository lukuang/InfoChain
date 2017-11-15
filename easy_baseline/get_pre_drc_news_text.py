"""
get news articles for the news crawled before drc project
"""

import os
import json
import sys
import re
import argparse
import codecs
sys.path.append("/infolab/node4/lukuang/code/InfoChain")
from data.pre_drc_data.news_data import PreDRCNews
from data.pre_drc_data.query import PreDRCQuery

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dest_dir")
    parser.add_argument("--day_limit","-dl",type=int,default=60)
    args=parser.parse_args()

    count = 0
    pre_drc_queries = PreDRCQuery().queries
    for qid in pre_drc_queries:
        query_string = pre_drc_queries[qid]
        print "Generating text for disaster:%s" %(query_string)
        single_disaster_news = PreDRCNews(qid,query_string,args.dest_dir,day_limit=args.day_limit)
        single_disaster_news.write_in_trec_format()
        count += 1
        print "There are %d queries yet to be processed" %(len(pre_drc_queries)-count)


if __name__=="__main__":
    main()

