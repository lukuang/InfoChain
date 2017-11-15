"""
handle news articles crawled before the DRC project
"""

import os
import json
import sys
import re
import argparse
import codecs
from bs4 import BeautifulSoup
from myUtility.indri import TextFactory
PATH_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),"path.json")

def get_date_from_file_name(day_file):
    m = re.search("^(\w+-\w+-\w+)-\w+",day_file)
    if m:
        return m.group(1)
    else:
        raise ValueError("mal-formatted file name %s" %(day_file))

class PreDRCNews(object):
    def __init__(self,qid,query_string,dest_dir,day_limit=60,data_path=None,
                 debug=False):
        if data_path:
            self._data_path = data_path
        else:
            path_data = json.load(open(PATH_FILE))
            self._data_path = path_data["data"]
        self._qid = qid
        self._debug = debug
        self._day_limit = day_limit
        self._src_dir = os.path.join(self._data_path,query_string,"news")
        self._dest_dir = os.path.join(dest_dir,qid)
        if not os.path.exists(self._dest_dir):
            os.mkdir(self._dest_dir)

    def write_in_trec_format(self):
        if not self._day_limit:
            self._day_limit = -1
        

        day_count = self._day_limit
        old_date = ""
        day_document_count = 0
        text_factory = None
        try:
            print self._src_dir
            day_files = sorted(os.walk(self._src_dir).next()[2])
        except StopIteration:
            print "No documents crawled yet for the query %s" %(self._qid)
            return
        else:
            for day_file in day_files:
                
                date =  get_date_from_file_name(day_file)
                if date != old_date:
                    if text_factory:
                        text_factory.write()

                    if self._day_limit == 0:
                        break
                    else:
                        print "write documents for date %s" %(date)
                        self._day_limit -= 1
                        old_date = date
                        day_document_count = 0
                        dest_file = os.path.join(self._dest_dir,date)
                        if os.path.exists(dest_file):
                            # if the text of a day is processed before,
                            # skip that day
                            continue
                        text_factory = TextFactory(dest_file)
                        day_document_count = 0
                else:
                    print "\tprocess file %s" %(day_file) 
                    dest_file = os.path.join(self._dest_dir,date)
                    if os.path.exists(dest_file):
                        # if the text of a day is processed before,
                        # skip that day
                        continue
                    news_file = os.path.join(self._src_dir,day_file)
                    try:
                        document_data = json.load(open(news_file))
                    except ValueError as e:
                        if re.search("Unterminated",str(e)):
                            print e
                            print "possible Json file error"
                            continue
                        else:
                            raise e
                    else:
                        for doc in document_data:
                            day_document_count += 1
                            did = "%s_%s_%s" %(self._qid,date,str(day_document_count))
                            try:
                                doc_text = doc["content"]
                            except KeyError:
                                print "Warning: missing content!"
                            else:
                                soup = BeautifulSoup(doc_text,"lxml")
                                for script in soup(["script", "style"]):
                                    script.extract()    # rip it out

                                document_text = re.sub("\n+","\n",soup.get_text())
                                if document_text:
                                    text_factory.add_document(did,document_text)
                                else:
                                    continue
                


                if self._debug:
                    break





def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qid","-q",default="PreDrc1")
    parser.add_argument("--day_limit","-dl",type=int,default=60)
    parser.add_argument("dest_dir")
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--query_string","-qs",default="Chile_quake")
    args=parser.parse_args()
    single_disaster_news = PreDRCNews(args.qid,args.query_string,args.dest_dir,day_limit=args.day_limit,debug=args.debug)
    single_disaster_news.write_in_trec_format()

if __name__=="__main__":
    main()

