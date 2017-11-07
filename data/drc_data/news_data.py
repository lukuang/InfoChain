"""
process news data of crawled drc data
"""

import os
import json
import sys
import re
import argparse
import codecs
from bs4 import BeautifulSoup
from myUtility.indri import TextFactory
# from myUtility.parser import Html_parser

PATH_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),"path.json")

class DRCNews(object):
    def __init__(self,qid,dest_dir,day_limit,news_path=None,
                 debug=False):
        if news_path:
            self._news_path = news_path
        else:
            path_data = json.load(open(PATH_FILE))
            self._news_path = path_data["news"]
        self._qid = qid
        self._debug = debug
        self._day_limit = day_limit
        self._src_dir = os.path.join(self._news_path,qid)
        self._dest_dir = os.path.join(dest_dir,qid)
        if not os.path.exists(self._dest_dir):
            os.mkdir(self._dest_dir)

    def write_in_trec_format(self):
        if not self._day_limit:
            self._day_limit = -1

        day_count = self._day_limit
        for date in sorted(os.walk(self._src_dir).next()[1]):
            print "write documents for date %s" %(date)
            dest_file = os.path.join(self._dest_dir,date)
            if os.path.exists(dest_file):
                # if the text of a day is processed before,
                # skip that day
                continue
            text_factory = TextFactory(dest_file)
            d = os.path.join(self._src_dir,date)
            for news_file in os.walk(d).next()[2]:
                did = "%s_%s_%s" %(self._qid,date,news_file)
                news_file = os.path.join(d,news_file)
                # document_text = html_parser.get_text(news_file)
                soup = BeautifulSoup(open(news_file).read(),"lxml")
                for script in soup(["script", "style"]):
                    script.extract()    # rip it out

                document_text = re.sub("\s+"," ",soup.get_text())
                if document_text:
                    text_factory.add_document(did,document_text)
                else:
                    continue
            text_factory.write()
            self._day_limit -= 1
            if self._day_limit == 0:
                break


            if self._debug:
                break






def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qid","-q",default="1")
    parser.add_argument("dest_dir")
    args=parser.parse_args()
    single_disaster_news = DRCNews(args.qid,args.dest_dir,debug=True)
    single_disaster_news.write_in_trec_format()

if __name__=="__main__":
    main()

