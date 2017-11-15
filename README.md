# InfoChain

The repository for the InfoChain Project

## Table of Contents
  - [Data](#data)
    - [Pre DRC](#pre-drc)
    - [DRC](#drc)
    - [Data Locations](#data-locations)
  - [Code](#code)
    - [Path](#path)
    - [Prerequisit](#prerequisit)
    - [Data Processing](#data-processing)
    - [Easy baseline](#drc)
      - [How it works](#how-it-works)
      - [How to run](#how-to-run)
      - [Some advice](#some-advice)
      - [Extra utilities](#extra-utilities)
    
    
    
## Data

 There are two data collections that I used:
 ### Pre DRC:    
  * news crawled before the DRC project using Yahoo! News API.  
  * try to crawl 100 news artiles per hour  
  * redundant articles (with same url as one of the previously stored articles) are ignored.
  
 ### DRC:  
  * news crawled during the DRC project
  * try to crawl 10 pages of results per day, and the results are limited to the day.
  * no url based redundancy detection is used
     
  
 ### Data Locations:  
  * Pre DRC: can be found in [data/pre_drc_data/path.json](https://github.com/lukuang/InfoChain/blob/master/data/pre_drc_data/path.json)  
      It includes the paths for news data and the queries.
      
  * DRC: can be found in [data/drc_data/path.json](https://github.com/lukuang/InfoChain/blob/master/data/drc_data/path.json)  
      It includes the paths for news data, tweets, and the queries.
  

## Code
  ### Path
  The code resides in Infolab at:```/infolab/node4/lukuang/code/InfoChain```
  
  ### Prerequisit
  In order to run the code, you need the have the [utility modules](https://github.com/lukuang/myUtility) I wrote before in   your python module search path. One way to do it is to include the path of the module to the PYTHONPATH enviroment variable:
  
  ```$ export PYTHONPATH=/path-contains-module:$PYTHONPATH```
  
  The software version requirements are: 
   * python: 2.7
   * Java: Java 8 (for Stanford NER)
   * Indri: 5.6
   
  ### Data Processing:  
  There are two modules for processing the two data collections:
   * [data/pre_drc_data](https://github.com/lukuang/InfoChain/blob/master/data/pre_drc_data)
     It contains the modules for processing the data related to the Pre DRC crawl. There are 4 files: 
      * \_\_init\_\_.py:  
      * news_data.py: containing classes for handling news articles in Pre DRC data 
      * query.py: processing the queries in the query file of the Pre DRC data 
      * path.json: json format file containing the paths for Pre DRC data
   * [data/drc_data](https://github.com/lukuang/InfoChain/blob/master/data/drc_data)
     It contains the modules for processing the data related to the DRC crawl. There are 4 files: 
      * \_\_init\_\_.py:  
      * news_data.py: containing classes for handling news articles in DRC data set 
      * twitter_data.py: intended for processing DRC tweet data, not finished yet 
      * query.py: processing the queries in the query file of the DRC data
      * path.json: json format file containing the paths for DRC data
      
  And two python scripts [easy_baseline/get_pre_drc_news_text.py](https://github.com/lukuang/InfoChain/blob/master/easy_baseline/get_pre_drc_news_text.py) and [easy_baseline/get_drc_news_text.py](https://github.com/lukuang/InfoChain/blob/master/easy_baseline/get_drc_news_text.py) for generating trec format text files for these two data set in preparation for building an Indri index from them. Fot these two scripts, two paramters can be taken:
  * dest_dr(required) : the destination directory for the text
  * -dl (optional): the number of days from the beginning of a disaster that you want the news article to be from. If no limit is wanted, do not use this parameter.
  
  For generating an Indri Index from the text files, please use the script [easy_baseline/generate_index_para.py](https://github.com/lukuang/InfoChain/blob/master/easy_baseline/generate_index_para.py), which takes three **required** parameters:  
  * index_path: the destination of the index that you want to generate  
  * data_path: the data directory path of the text files (refering to the _dest\_dr_ mentioned above).
  * para_file_path: the path of the Indri parameter file as the output of this script
  
  Once the parameter file is generated, use the following command to generate the index
  
  ```$ IndriBuildIndex para_file_path```
  
  ### Easy Baseline
  #### How it works
  I implement a very simple implementation ([easy_baseline/easy_baseline.py](https://github.com/lukuang/InfoChain/blob/master/easy_baseline/easy_baseline.py)) to find common entities of two disaster instances that relies only on the occurrence counts. The workflow is as follow:  
  1. A User will input two queries to the script.  
  2. The script will search the two queries against the Indri index generated above.  
  3. If there are common documents in the top 10 documents, return the document ids.
  4. If there are no common documents, first generate the vector representations of each of the top 100 documents. The vectors are the occurrence counts of words or entities in the document. There are three ways to generate the vector:  
      * use individual words.  
      * use the name entities identified by Stanford NER.  
      * use the entities found by the [Dbpedia Spotlight's](https://github.com/dbpedia-spotlight/dbpedia-spotlight) web api to find Wikipedia entities in the document.  
  5. Merge the document vectors for each query. Compare the total vectors of the two queries to find common entities that within the 100 most frequent entities of each query. Record the entities and their **smaller** occurrence counts for one of the querie. 
  6. The common entities will be printed to the standard output as (entity,smaller count) tuples.
  7. The entities as well as the documents mentioning the entities will be output as a json format in the file  ```/infolab/node4/lukuang/code/InfoChain/easy_baseline/data/results/easy_basline/METHOD_NAME/QUERY_STRING``` where the ```METHOD_NAME``` is the method used for generating vectors(words,stanford ner, etc.), and the ```QUERY_STRING``` is the combination of the query strings in which the queries are ordered alphabetically in order to be combined.
  
  #### How to run
  Two required parameters:   
  * query_1  
  * query_2
    
  Optional parameters:  
  * -td: top document count, the number of documents in which the script trys to find common documents  
  * -cd: common info doc count, the number of documents in which the script trys to find common entities  
  * -nt: number of top common info: the number of most frequent entities to be considered when finding common entities. For instance, if it is specified as 100, the most frequent 100 entities of each query will be compared and the common entities will be printed out   
  * *-vm*: vector method, what kind of vectors to be generated. The input options are:  
    * 0: words  
    * 1: Stanford NER  
    * 2: Dbpedia Spotlight  
  * -rd: result dir, the result directory that the entities as well as the documents containing them should be stored to  
  * -vd: vector dir, the vector directory that the intermediate document vector results will be stored to.  
  * -ind: index dir, the index directory that the queries will be searched against.  
  * -tqf: temporal query file, the temporal Indri query parameter file
  
  #### Some advice
  Feel free to execute multiple instances with **different** vector method. However, executing multiple instances with same vector might be a bad idea since they might try to read/write the document vector information at the same time.
  
  #### Extra utilities
  There is a script [easy_baseline/view_entity.py](https://github.com/lukuang/InfoChain/blob/master/easy_baseline/view_entity.py) through which you can show the surranding text of a common entities to get an idea about how the entity is used in the two disasters.There are three parameters of it:  
  * disaster_vector_result_file (required): the result file generated by easy_baseline.py  
  * entity (required): the name of the entitiy that you want to show
  * -ind (optional): the Indri index path
  
  
  
      
      
      
  
  
  

