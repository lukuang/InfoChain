# encoding=utf8  
"""
easy baseline for InfoChain project
"""
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
import os
import json
import re
import argparse
import codecs
import subprocess
from collections import Counter
import requests
from abc import ABCMeta,abstractmethod
from enum import IntEnum, unique
# from nltk.tokenize import sent_tokenize
from myUtility.indri import IndriQueryFactory



@unique
class VectorMethod(IntEnum):
    use_words = 0
    stanford_ner = 1
    dbpedia = 2
    

class EntityGenerator(object):
    """
    base class for entity generation
    """
    __metaclass__ = ABCMeta
    def __init__(self,index_dir):
        self._index_dir = index_dir


    @abstractmethod
    def _get_entity_vector_from_text(self,text):
        pass

    def get_entity_vector_from_did(self,did):
        entities = {}
        text = get_text_from_did(did,self._index_dir)
        if text:
            entities = self._get_entity_vector_from_text(text,did)
        return entities


class StanfordEntityGenerator(EntityGenerator):
    def __init__(self,index_dir,query_suffix):
        super(StanfordEntityGenerator,self).__init__(index_dir)
        self._temp_file = "/tmp/ner_temp-"+query_suffix+".txt"
        self._run_command = ["bash","/infolab/node4/lukuang/code/stanford-ner-2017-06-09/ner.sh","%s" %(self._temp_file)]


    def _get_entity_vector_from_text(self,text,did):
        entities = {}
        with codecs.open(self._temp_file,"w",'utf-8') as f:
            f.write(text.decode('utf-8'))
        with open(os.devnull, 'w') as null_file: 
            p = subprocess.Popen(self._run_command,stdout=subprocess.PIPE,stderr=null_file)
        previous_text = ""
        previous_tag = ""
        while True:
            line = p.stdout.readline()
            if line != '':
                line = line.strip()
                word_tag_pairs = line.split()
                for pair in word_tag_pairs:
                    m = re.search("^(.+)/([^/]+)$",pair)
                    if m :
                        word = m.group(1)
                        tag = m.group(2)
                        if tag != "O":
                            if tag == previous_tag:
                                previous_text = "%s %s" %(previous_text,word)
                            else:
                                
                                if previous_text:
                                    if previous_text not in entities:
                                        entities[previous_text] = 0
                                    entities[previous_text] += 1
                                    # print "%s %s" %(previous_text,previous_tag)
                                previous_text = word
                                previous_tag = tag
                        else:
                            if previous_text:
                                if previous_text not in entities:
                                        entities[previous_text] = 0
                                entities[previous_text] += 1
                                # print "%s %s" %(previous_text,previous_tag)
                                previous_text = ""
                                previous_tag = ""


                    else:
                        print "no infor found %s" %(pair)

            else:
                if previous_text:
                    if previous_text not in entities:
                            entities[previous_text] = 0
                    entities[previous_text] += 1
                break
        return entities

class DbpediaEntityGenerator(EntityGenerator):
    def __init__(self,index_dir,query_suffix):
        super(DbpediaEntityGenerator,self).__init__(index_dir)
        self._temp_file = "/tmp/dbpedia_temp-"+query_suffix+".txt"
        self._run_command = ["bash","/infolab/node4/lukuang/code/stanford-ner-2017-06-09/parse.sh","%s" %(self._temp_file)]
        self._url_base = "http://model.dbpedia-spotlight.org/en/annotate"
        self._headers = {'accept': 'application/json'}

    def _get_entity_vector_from_text(self,text,did):
        entities = {}
        with codecs.open(self._temp_file,"w",'utf-8') as f:
            f.write(text.decode('utf-8'))
        with open(os.devnull, 'w') as null_file: 
            p = subprocess.Popen(self._run_command,stdout=subprocess.PIPE,stderr=null_file)

        while True:
            sentence = p.stdout.readline()
            if sentence != '':
                # print sentence
                # print "-"*10
                params = {"text":sentence}
                r = requests.get(self._url_base,params=params,headers=self._headers)
                if r.status_code == requests.codes.ok:
                    try:
                        raw_entities = r.json()["Resources"]
                    except KeyError:
                        # print "No entities found for did %s" %(did)
                        # print text
                        # print r.json()
                        # print '-'*20
                        pass
                    else:
                        for entity_info in raw_entities:
                            try:
                                entity_name = entity_info["@surfaceForm"]
                            except KeyError:
                                print "No surface name for entity"
                                print entity_info
                                print '-'*20
                            else:
                                if entity_name not in entities:
                                    entities[entity_name] = 0
                                entities[entity_name] += 1
                else:
                    raise RuntimeError("get error when requesting for did %s with error code %s\n%s" 
                                        %(did, r.status_code,r.url)
                                    )
            else:
                break
        # print entities
        return entities


class Vectors(object):
    def __init__(self,vector_method,vector_dir,index_dir,query_suffix):
        self._vector_method = vector_method
        self._query_suffix = query_suffix
        self._index_dir = index_dir
        if vector_method != VectorMethod.use_words:
            Entity_Generators = {
                VectorMethod.stanford_ner : StanfordEntityGenerator,
                VectorMethod.dbpedia : DbpediaEntityGenerator

            }
            self._entity_generator = Entity_Generators[self._vector_method](self._index_dir,self._query_suffix)


        self._vector_dir = os.path.join(vector_dir,self._vector_method.name)
        if not os.path.exists(self._vector_dir):
            os.mkdir(self._vector_dir)
        self._has_new_vectors = set()
        self._vectors = {}

    def _get_qid_from_did(self,did):
        m = re.match("^([^-]+?)_",did)
        if m:
            return m.group(1)
        else:
            raise ValueError("The qid %s is mal-formatted" %(qid))

    def try_to_load(self,results):
        for input_qid in results:
            for did in results[input_qid]:
                qid = self._get_qid_from_did(did)             
                if qid not in self._vectors: 
                    self._vectors[qid] = {}
                    query_vector_file = os.path.join(self._vector_dir,qid)

                    if os.path.exists(query_vector_file):
                        self._vectors[qid] = json.load(open(query_vector_file))
                        if did not in self._vectors[qid]:
                            self._vectors[qid][did] = self._get_vector_from_did(did)
                            self._has_new_vectors.add(qid)
                    else:
                        self._vectors[qid][did] = self._get_vector_from_did(did)
                        self._has_new_vectors.add(qid)
                else: 
                    if did not in self._vectors[qid]:
                        self._vectors[qid][did] = self._get_vector_from_did(did)
                        self._has_new_vectors.add(qid)



    def _get_vector_from_did(self,did):
        if self._vector_method == VectorMethod.use_words:
            return get_word_vector_from_did(did,self._index_dir)
        else:
            return self._entity_generator.get_entity_vector_from_did(did)

    def __getitem__(self, did):
        qid = self._get_qid_from_did(did)
        return self._vectors[qid][did]

    def store(self):
        if self._has_new_vectors:
            for qid in self._has_new_vectors:
                query_vector_file = os.path.join(self._vector_dir,qid)
                with open(query_vector_file,"w") as f:
                    f.write(json.dumps(self._vectors[qid]))


def generate_temp_query_file(index_dir,temp_query_file,
                             common_info_doc_count,query_1,query_2):
    query_factory = IndriQueryFactory(common_info_doc_count,rule="f2exp")
    queries = {
        "1":query_1,
        "2": query_2
    }
    query_factory.gene_normal_query(temp_query_file,queries,index_dir)


def run_temp_query(temp_query_file):
    run_command = [
        "IndriRunQuery",
        temp_query_file
    ]
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE)
    results = {}
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            docid = parts[2]
            if qid not in results:
                results[qid] = []
            results[qid].append(docid)

        else:
            break 
    return results

def find_common_top_document(results,top_document_count):
    common_top_document = []
    qid1 = results.keys()[0]
    qid2 = results.keys()[1]
    sub_results_1 = results[qid1][:top_document_count]
    sub_results_2 = results[qid2][:top_document_count]

    for did in sub_results_1:
        if did in sub_results_2:
            common_top_document.append(did)
    return common_top_document

def get_text_from_did(did,index_dir):
    run_command = "dumpindex %s  dt `dumpindex %s di docno %s`" %(index_dir,index_dir,did)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    doc_all_info = p.communicate()[0]
    m = re.search("<TEXT>(.+)</TEXT>",doc_all_info,re.DOTALL) 
    if m:
        doc_text = m.group(1)
        doc_text = unicode(doc_text, errors='ignore')

        return doc_text
    else: 
        return None 


def get_word_vector_from_did(did,index_dir):
    run_command = "dumpindex %s  dv `dumpindex %s di docno %s`" %(index_dir,index_dir,did)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    vocab_list = p.communicate()[0]
    lines = vocab_list.split("\n")
    lines = lines[2:] 
    words = {}
    for line in lines:
        if not line:
            break
        parts = line.split()
        
        w = parts[2]
        if w != "[OOV]":
            if w not in words:
                words[w] = 0
            words[w] += 1

    return words


# def get_top_documents(results,common_info_doc_count):
#     top_documents = {}
#     for qid in results:
#         top_documents[qid] = results[qid][:common_info_doc_count]
    
#     return top_documents

def get_top_vector(results,vectors):
    total_vectors = {}
    top_document_vectors = {}
    for qid in results:
        total_vectors[qid] = {}
        top_document_vectors[qid] = {}
        for did in results[qid]:
            top_document_vectors[qid][did] = vectors[did]
            for w in top_document_vectors[qid][did]:
                if w in total_vectors[qid]:
                    total_vectors[qid][w] += top_document_vectors[qid][did][w]
                else:
                    total_vectors[qid][w] = top_document_vectors[qid][did][w]

            

    return top_document_vectors, total_vectors 

# def get_top_document_word_vector(top_documents,index_dir):
#     total_vectors = {}
#     top_document_vectors = {}
#     for qid in top_documents:
#         total_vectors[qid] = {}
#         top_document_vectors[qid] = {}
#         for did in top_documents[qid]:
#             top_document_vectors[qid][did] = get_word_vector_from_did(did,index_dir)
#             for w in top_document_vectors[qid][did]:
#                 if w in total_vectors[qid]:
#                     total_vectors[qid][w] += top_document_vectors[qid][did][w]
#                 else:
#                     total_vectors[qid][w] = top_document_vectors[qid][did][w]

            

#     return top_document_vectors, total_vectors 

# def get_top_document_entity_vector(top_documents,entity_generator):
#     total_vectors = {}
#     top_document_vectors = {}
#     for qid in top_documents:
#         total_vectors[qid] = {}
#         top_document_vectors[qid] = {}
#         for did in top_documents[qid]:
#             top_document_vectors[qid][did] = entity_generator.get_entity_vector_from_did(did)
#             for w in top_document_vectors[qid][did]:
#                 if w in total_vectors[qid]:
#                     total_vectors[qid][w] += top_document_vectors[qid][did][w]
#                 else:
#                     total_vectors[qid][w] = top_document_vectors[qid][did][w]

            

#     return top_document_vectors, total_vectors


def find_top_common_terms(total_vectors,num_of_top_common_info):
    query_1_word_counter = { w:c for w,c in Counter(total_vectors.values()[0]).most_common(num_of_top_common_info) }
    query_2_word_counter = { w:c for w,c in Counter(total_vectors.values()[1]).most_common(num_of_top_common_info) }
    top_common_terms = {}
    # print query_1_word_counter
    # print query_2_word_counter
    for w in query_1_word_counter:
        if w in query_2_word_counter:
            top_common_terms[w] = min(query_1_word_counter[w],query_2_word_counter[w])
    return top_common_terms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_1")
    parser.add_argument("query_2")
    parser.add_argument("--top_document_count","-td",type=int,default=10)
    parser.add_argument("--common_info_doc_count","-cd",type=int,default=100)
    parser.add_argument("--num_of_top_common_info","-nt",type=int,default=100)
    parser.add_argument("--vector_method","-vm",choices=range(3),default=0,type=int,
        help="""
            Choose the predictor:
                0: use_words
                1: stanford_ner
                2: dbpedia
            """)
    parser.add_argument("--result_dir","-rd",default="/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/results/easy_basline")
    parser.add_argument("--vector_dir","-vd",default="/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/news/vectors")
    parser.add_argument("--index_dir","-ind",default="/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/news/index")
    parser.add_argument("--temp_query_file","-tqf",default="/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/news/indri_para/temp_query_file")
    args=parser.parse_args()

    args.vector_method = VectorMethod(args.vector_method)
    

    generate_temp_query_file(args.index_dir,args.temp_query_file,
                             args.common_info_doc_count,args.query_1,args.query_2)

    results = run_temp_query(args.temp_query_file)
    # print results
    common_top_document = find_common_top_document(results,args.top_document_count)

    if args.query_1 > args.query_2:
        query_suffix = re.sub(" ","_",args.query_1) + "-" + re.sub(" ","_",args.query_2)
    else:
        query_suffix = re.sub(" ","_",args.query_2) + "-" + re.sub(" ","_",args.query_1)


    if common_top_document:
        print "common documents in top %d are found:" %(args.top_document_count)
        for did in common_top_document:
            print "\t%s" %(did)

    else:
        print "no common in top %d documents" %(args.top_document_count)
        # top_documents = get_top_documents(results,args.common_info_doc_count)

        vectors = Vectors(args.vector_method,args.vector_dir,args.index_dir,query_suffix)
        vectors.try_to_load(results)
        vectors.store()
        top_document_vectors, total_vectors = get_top_vector(results,vectors)

        # if args.vector_method == VectorMethod.use_words:
        #     top_document_vectors, total_vectors = get_top_document_word_vector(
        #                                                 top_documents,args.index_dir)
            
        # else:

        #     entity_generator = Entity_Generators[args.vector_method](args.index_dir,query_suffix)

        #     top_document_vectors, total_vectors = get_top_document_entity_vector(
        #                                                 top_documents,entity_generator)
            # print total_vectors
        

        top_common_terms = find_top_common_terms(total_vectors,args.num_of_top_common_info)
        document_id_vecotr = {}
        for w in top_common_terms:
            document_id_vecotr[w] = {
                                        "1":[],
                                        "2":[],
                                    }
        for qid in top_document_vectors:
            for did in top_document_vectors[qid]:
                for w in top_common_terms:
                    if w in top_document_vectors[qid][did]:
                        document_id_vecotr[w][qid].append(did)


        # store result
        document_id_vecotr_store_file = os.path.join(args.result_dir,args.vector_method.name,query_suffix)

        with open(document_id_vecotr_store_file,"w") as f:
            f.write(json.dumps(document_id_vecotr,indent=4))

        print sorted(top_common_terms.items(),key=lambda x:x[1])

if __name__=="__main__":
    main()

