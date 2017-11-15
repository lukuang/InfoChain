# InfoChain

The repository for the InfoChain Project

## Table of Contents
  - [Data](#data)
    - [Pre DRC](1.pre-drc)
    - [DRC](2.drc)
    
    
    
## Data

 There are two data collections that I used:
  1. Pre DRC:  
     * news crawled before the DRC project using Yahoo! News API.  
     * try to crawl 100 news artiles per hour  
     * redundant articles (with same url as one of the previously stored articles) are ignored.
  
  2. DRC:
     * news crawled during the DRC project
     * try to crawl 10 pages of results per day, and the results are limited to the day.
     * no url based redundancy detection is used
     
  The paths of data can be found in code section.
