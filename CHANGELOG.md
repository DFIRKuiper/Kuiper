# **Changelog**
This page list the Changelog for Kuiper project
## **[2.3.5] - 2023-11-18**
### **Fixes:**
- Bug Fix: improve api results [Pull Request #113](https://github.com/DFIRKuiper/Kuiper/pull/113)
- Bug Fix: fix redis Dockerfile [Pull Request #108](https://github.com/DFIRKuiper/Kuiper/pull/108)
- Bug Fix: fix path traversal vulnerability when extracting tar files [Pull Request #106](https://github.com/DFIRKuiper/Kuiper/pull/106)
- Bug Fix: fix issue with extracting the compressed zip file
- Bug Fix: fix issue with data including quoting [Kuiper modifies meaning of parsed data (quoting)](https://github.com/DFIRKuiper/Kuiper/issues/107)

## **[2.3.4] - 2023-02-03**
### **Fixes:**
- Bug Fix: Flask and Celery Docker Images (changed gevent to version 1.2.2) [Pull Request #85](https://github.com/DFIRKuiper/Kuiper/pull/85)
- Bug Fix: fixed system health scheduler script 
- Changed the Elasticsearch Java options from `ES_JAVA_OPTS=-Xms512m -Xmx512m` to `ES_JAVA_OPTS=-Xms4g -Xmx4g`
### **Added:**
- Net Logon parser parser [Pull Request #86](https://github.com/DFIRKuiper/Kuiper/pull/86)
- Add machine select box to alerts page [Pull Request #88](https://github.com/DFIRKuiper/Kuiper/pull/88)


## **[2.3.3] - 2022-10-15**
### **Fixes:**
- Fixed the update of machines processing progress to be calculated in server side instead of client side

### **Added:**
- PCAP parser
- iOS Mobile Forensics Parsers `ios_*`
- SDS parser (Security Descriptor Stream)
- build new docker image for `celery` and `flask` version `2.3.2`


## **[2.3.2] - 2022-08-13**
### **Fixes:**
- Fixed the Autoruns parsers files (thanks to @mayHamad)

### **Added:**
- Add Search, Add extra column, and Group by for the Rhaegal alerts in browser artifacts
- Timeline views
- Autoruns parsers (thanks to @mayHamad)
- Fennec parser for linux artifacts (thanks to @AbdulRhmanAlfaifi)
- SEP (Symantec Endpoint Protection) logs parser (thanks to @mnr-hmm)

### **Removed:**
- Removed the NFS service, and use only docker volumes directly (if you want to run the services in different machines, enable the nfs service in docker-compose.yaml)



## **[2.3.1] - 2022-02-07**
### **Fixes:**
- Fixed dynamic add for folder `kuiper/app/parsers/temp`
- Fixed issue of uploading files to a previously created machine
- Fixed issue of handling error message in elasticsearch version 7.16.2 during the indexing
- Fixed issue to preserve the selected record in browse artifact table if detailed table clicked
- Fixes the system health for celery if the task has large number of arguments



## **[2.3.0] - 2022-01-25**

### **Added:**
- Export the browsed artifacts records from the interface (only the displayed columns).
- Add group by aggregation search query for specific fields.
- Search by machine group for artifacts from the list of machines.
- Added load spinner for browse artifacts interface during the load for artifacts.
- Export tagged records as a xlsx timeline based on previously built "views".
- Support multiple type of tags (malicious, suspicious, and legit) - use keyboard "M", "S", and "L" respectively.
- Add dynamic extra column to the browse artifact table.
- Support Elasticsearch query string regex format for browse artfacts search.
- Add configuration for timeline views (`Settings` -> `Configuration` -> `Timeline Views`) - only few samples included in this version.
- Added Rhaegal icon on the browse artifacts table as indication of Rhaegal alert triggered for each record (`red` - triggered, `white` - not triggered)
- Add ability to close Elasticsearch index to reduce the memory utilization (from the case card, click `edit`, then select `Not Active`, and `Submit`)
    you will not be able to search for any records inside that case, and you cannot process the machines inside it.
    to open the case, change the case status to `Active`.
- All Kuiper docker images (`flask`, `celery`, `nginx`, `NFS`, `es01`, `mongodb`, and `redis`) has been pushed to (Dockerhub)[https://hub.docker.com/u/dfirkuiper]. To install Kuiper, simply run `docker-compose pull` then `docker-compose up -d`
- Added new parsers 
    - **IIS Access Logs:** by @heck-gd ([https://github.com/heck-gd](https://github.com/heck-gd))
    - **Exchange Logs:** by @heck-gd ([https://github.com/heck-gd](https://github.com/heck-gd))
    - **UserAccessLogging:** by @muteb ([https://github.com/muteb](https://github.com/muteb))
    - **osqueryIR (`34` parsers for Linux):** by @AbdulRhmanAlfaifi ([https://github.com/AbdulRhmanAlfaifi/osqueryIR](https://github.com/AbdulRhmanAlfaifi/osqueryIR))


### **Changed:**
- Fixed bugs on search browse artifacts.
- Enhanced parsers.

### **Fixes:**
- Fixed the timeline view export to support unicode data (error faced during exporting Recyclebin `Data.Path` which is unicode)
