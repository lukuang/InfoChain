# InfoChain

The repository for the InfoChain Project

## Table of Contents
  - [Data](#data)
    - [Pre DRC](#pre-drc)
    - [DRC](#drc)
    - [Data Locations](#data-locations)
  - [Code](#code)
    - [Prerequisit](#prerequisit)
    - [Data Processing](#data-processing)
    - [Easy baseline](#drc)
    
    
    
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
  ## path 
  ### Prerequisit
  In order to run the code, you need the have the [utility modules](https://github.com/lukuang/myUtility) I wrote before in   your python module search path. One way to do it is to include the path of the module to the PYTHONPATH enviroment variable:
  
  ```$ export PYTHONPATH=/path-contains-module:$PYTHONPATH```
  ### Data Processing:  
  There are two modules for processing the two data collections:
   * InfoChain/data/pre_drc_data
     It contains the modules for processing the data related to the Pre DRC crawl. There are 3 files: 
      * \_\_init\_\_.py:  
      * news_data.py: containing classes for handling news article data crawl  
      * twitter_data.py: intended for processing DRC tweet data, not finished yet 
      * path.json: json format file containing the paths for drc data
   * InfoChain/data/drc_data
     It contains the modules for processing the data related to the DRC crawl. There are 4 files: 
      * \_\_init\_\_.py:  
      * news_data.py: containing classes for handling news article data crawl  
      * twitter_data.py: intended for processing DRC tweet data, not finished yet 
      * query.py: processing the queries in the query file of the DRC data
      * path.json: json format file containing the paths for drc data
      
      
      
  
  
  

