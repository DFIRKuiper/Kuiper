

![logo.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/logo2.png?raw=true)


## Table of Contents

<!-- TOC depthFrom:2 -->


- [1. Kuiper](#kuiper)
    - [1.1. What is Kuiper?](#what-is-kuiper)
    - [1.2. Why Kuiper?](#why-kuiper)
    - [1.3. How Kuiper Will Help Optimize the Investigation?](#How-Kuiper-Will-Help-Optimize-the-Investigation)
    - [1.4. Use Cases](#Use-Cases)
- [2. Examples](#Examples)
- [3. Kuiper Components](#Kuiper-Components)
    - [3.1. Components Overview](#Components-Overview)
    - [3.2. Parsers](#Parsers)
- [4. Getting Started](#getting-started)
    - [4.1. Requirements](#requirements)
    - [4.2. Installation](#Installation)
    - [4.3. Adding Custom Parser](#addingParser)
- [5. Issues Tracking and Contribution](#Issues-Tracking-and-Contribution)
- [6. Licenses](#Licenses)
- [7. Authors](#Authors)

    


<!-- /TOC -->


# Kuiper

Digital Investigation Platform


## What is Kuiper?
Kuiper is a digital investigation platform that provides a capabilities for the investigation team and individuals to parse, search, visualize collected evidences (evidences could be collected by fast triage script like [Hoarder](https://github.com/muteb/Hoarder)). In additional, collaborate with other team members on the same platform by tagging artifacts and present it as a timeline, as well as setting rules for automating the detection. The main purpose of this project is to aid in streamlining digital investigation activities and allow advanced analytics capabilities with the ability to handle a large amounts of data. 

![diagram.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/Diagram.png?raw=true)


## Why Kuiper?
Today there are many tools used during the digital investigation process, though these tools help to identify the malicious activities and findings, as digital analysts there are some shortages that needs to be optimized:

- Speeding the work flow.
- Increase the accuracy.
- Reduce resources exhaustion.

With a large number of cases and a large number of team members, it becomes hard for team members collaboration, as well as events correlation and building rules to detect malicious activities. Kuiper solve these shortages. 


## How Kuiper Will Help Optimize the Investigation?
- **Centralized server**: Using a single centralized server (**Kuiper**) that do all the processing on the server-side reduce the needed hardware resources (CPU, RAM, Hard-disk) for the analysts team, no need for powerful laptop any more. In addition, all evidences stored in single server instead of copying it on different machines during the investigation.
- **Consistency**: Depending on different parsers by team members to parse same artifacts might provide inconsistency on the generated results, using tested and trusted parsers increases the accuracy.
- **Predefined rules**: Define rules on Kuiper will save a lot of time by triggering alerts on past, current, and future cases, for example, creating rule to trigger suspicious encoded PowerShell commands on all parsed artifacts, or suspicious binary executed from temp folder, within **Kuiper** you can defined these rules and more.
- **Collaboration**: Browsing the parsed artifacts on same web interface by team members boost the collaboration among them using **tagging** and **timeline** feature instead of every analyst working on his/her own machine.


## Use Cases

 - **Case creation**: Create cases for the investigation and each case contain the list of machines scoped.
 - **Bulk evidences upload**: Upload multiple files (artifacts) collected from scoped machines via [Hoarder](https://github.com/muteb/Hoarder), [KAPE](https://www.kroll.com/en/services/cyber-risk/investigate-and-respond/kroll-artifact-parser-extractor-kape), or files collected by any other channel.
 - **Evidence processing**: Start parsing these artifact files concurrently for selected machines or all.
 - **Holistic view of evidences**: Browse and search within the parsed artifacts for all machines on the opened case.
 - **Rules creation**: Save search query as rules, these rules could be used to trigger alerts for future cases.
 - **Tagging and timeline**: Tag suspicious/malicious records, and display the tagged records in a timeline. For records or information without records (information collected from other external sources such as FW, proxy, WAF, etc. logs) you can add a message on timeline with the specific time.
 - **Parsers management**: Collected files without predefined parser is not an issue anymore, you can write your own parser and add it to Kuiper and will parse these files. read more how to add parser from [Add Custom Parser](https://github.com/DFIRKuiper/Kuiper/wiki/Add-Custom-Parser)



# Examples

**Create cases and upload artifacts**
![create_cases](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/create_case_upload_machines.gif?raw=true)

**Investigate parsed artifacts in Kuiper**
![create_cases](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/analysis.gif?raw=true)




# Kuiper Components

## Components Overview

Kuiper use the following components:

- **Flask:** A web framework written in Python, used as the primary web application component. 

- **Elasticsearch:** A distributed, open source search and analytics engine, used as the primary database to store parser results.

- **MongoDB:** A database that stores data in JSON-like documents that can vary in structure, offering a dynamic, flexible schema, used to store Kuiper web application configurations and information about parsed files. 

- **Redis:** A in-memory data structure store, used as a database, cache and message broker, used as a message broker to relay tasks to celery workers.

- **Celery:** A asynchronous task queue/job queue based on distributed message passing, used as the main processing engine to process relayed tasks from redis.

- **Gunicorn:** Handle multiple clients HTTPs requests

# Getting Started

## Requirements

- **OS:** 64-bit Ubuntu 18.04.1 LTS (Xenial)  (preferred)
- **RAM:**  4GB (minimum), 64GB (preferred)
- **Cores:** 4 (minimum)
- **Disk:** 25GB for testing purposes and more disk space depends on the amount of data collected.

**Notes**
- If you want to use RAM more than 64GB to increase Elasticsearch performence, it is recommended to use multiple nodes for Elasticsearch cluster instead in different machines
- For parsing, Celery generate workers based on CPU cores (worker per core), each core parse one machine at a time and when the machine finished, the other queued machines will start parsing, if you have large number of machines to process in the same time you have to increase the cores number

## Installation 

Starting from version 2.2.0, Kuiper now run over dockers, there are 7 dockers:

- **Flask**: the main docker which host the web application (check [docker image](https://hub.docker.com/r/dfirkuiper/dfir_kuiper)).
- **Mongodb**: stores the cases and machines metadata.
- **Elasticsearch (es01)**: stores the parsed artifacts data.
- **Nginx**: reverse proxy for the flask container.
- **Celery**: artifacts parser component check [docker image](https://hub.docker.com/r/dfirkuiper/dfir_kuiper).
- **Redis**: queue for celery workers
- **NFS (Network File System)**: container that stores the shared files between Flask and Celery containers.

To run the docker use the following command:

```shell
docker-compose up -d
```

### Issues

1 - **Note**: when you first run the dockers, Elasticsearch will fail to run and give the following error

```
ERROR: [1] bootstrap checks failed
[1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
```

To solve the issue run the command

```shell
sysctl -w vm.max_map_count=262144
```

2- Note: if you faced the following issue

```shell
Creating network "kuiper_kuiper" with driver "bridge"
Creating kuiper_es01    ... done
Creating kuiper_mongodb ... done
Creating kuiper_redis   ... done
Creating kuiper_flask   ... error
Creating kuiper_nfs     ... done
Creating kuiper_celery  ... 

ERROR: for kuiper_flask  Cannot start service flask: error while mounting volume '/var/lib/docker/volumes/kuiper_kuiper_nfs/_data': failed to mount local volume: mount :/:/var/lib/docker/vCreating kuiper_celery  ... done
```

To solve the issue, run the docker again:

```shell
docker-compose up -d
```

### Issues

1 - **Note**: when you first run the dockers, Elasticsearch will fail to run and give the following error
```
ERROR: for flask  Cannot start service flask: error while mounting volume '/var/lib/docker/volumes/kuiper_kuiper_nfs/_data': failed to mount local volume: mount :/:/var/lib/docker/volumes/kuiper_kuiper_nfs/_data, data: addr=172.30.250.10: permission denied
ERROR: Encountered errors while bringing up the project.
```

To solve the issue, run the command again 

```shell
docker-compose up -d
ERROR: [1] bootstrap checks failed
[1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
```
# Add Custom Parser

## Overview
A parser is a script used to read a row data (artifacts) to parse it and return the results on a structured format that are understandable by Kuiper, such as reading the Windows Events row files (.evtx) and return the result on a readable and understandable format for Kuiper to present it on the case. Kuiper store all parsed data in Elasticsearch, so it will be stored as JSON format. 

## Instructions

### 1. List All parsers

To list all parsers, go to (Administrator Panel -> Configuration) then click the (Parsers) tab.

![parsers.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/parsers_list.png?raw=true)


### 2. Add New Parser
In parser page, click on the (+) button.

![addparser.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/add_parser.png?raw=true)

Fill the input fields as following:
1.	**Parser Name**: make sure it does not contain spaces or special characters, only (letters, numbers, _)
2.	**Parser Description**
3.	**Parser File**: select the list of files and compress it in a zip file and upload it, make sure the files on the zip file directly not inside a folder.

![addparser.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/parser_zip_content.png?raw=true)

4.	**Parser Important Fields**: here you can select multiple fields that will show on the (browser artifacts) page.

![addparser.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/browser_artifacts_important_fields.png?raw=true)

The field path contains the data json path, example of Windows Events

![addparser.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/add_parser_importants_fields.png?raw=true)

5.	**Parser Interface**
* 	The parser should have a python file **Interface File** that contains the **interface function** that Kuiper will call it at the very beginning to start the parsing process. 
* 	The interface function is the one responsible for returning the list of JSON to Kuiper. Each JSON represents a record on the database in the form of `[{"Field A": "value 1", "Field B": "Value 2", "@timestamp": "2021-08-12T11:27:42.836598"},{"Field A": "Value 1", "Field B": "Value 2", "@timestamp": "2021-08-12T11:27:42.836598"}]` 
* 	If there are no records, the parser should return an empty list [].
* 	If parser failed, return (None).

* 	The function should have two parameters (file: the file's path to be parsed, parser: is the parser name).
* 	The interface function should be called inside the interface file, passing the file name to be parsed with the parser name.
* 	If the file name is not constant, no need to call the interface function; just use `def auto_interface (file, parser):` and the Kuiper parser manager will call this function and pass both values.
* 	Each JSON record on the returned list should include a field named (@timestamp) used on the timeline artifact browser pages. (@timestamp) is picked to best represent each parser (e.g., @timestamp for MFT is equivalent to FNCreated).


![addparser.png](https://github.com/DFIRKuiper/Kuiper/blob/master/img/v2.0.0/add_parser_interface_function.png?raw=true)

6.	**Parser Type**: OS General, Web Browser, Program Execution, Logging Information, User Activities, etc.

7.	**File Categorization (comma separated)**: this is how the parser engine will identify if the files exist should be parsed by this parser or not, such as extension (.evtx), file_name (\$MFT), startswith (\$I), magic_number (file content start with provided hex value)

## Testing environment
* 	Download Kuiper VM and test it on your machine https://github.com/DFIRKuiper/Kuiper/tree/master/VirualMachine
* 	Use the command `ip addr` to check what is the assigned IP address for Kuiper and then on your browser enter https://[ip-address]:8000/admin
    *  	If it does not work, 
        * 	Make sure your network IP and Kuiper IP are in the same network.
        * 	Check the assigned port number for Kuiper.
        * 	Try https://0.0.0.0:8000/admin/ 

* 	While testing, if you wish to edit the parser, the new changes will not be applied unless the service is stopped then started again. Run the following commands in Kuiper VM to reflect the changes:


```
./kuiper_install.sh -stop
./kuiper_install.sh -run
```

* 	If you want to run the same parser again on a file that has been already parsed using the same parser, Kuiper will not do it. (parsed files cannot be parsed again using the same parser)
    * 	Solution;
        * 	Upload the file using a different name.
        * 	Or, make a new machine and upload the desired file, then run the parser.
## Writing a parser using python3
Kuiper can understand only Python 2.6, when writing a parser using python 3, some modification should be added to the code so that Kuiper can process it. Code below shows an example of interface function for a parser written using Python 3 

![image](https://user-images.githubusercontent.com/54886091/130059100-55957549-6634-4744-8c8e-f92ce0ca215e.png)

```
def auto_interface(file,parser):
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        cmd = 'python3 '+ CurrentPath + parser + ' -f "' + file.replace("$" , '\$') + '"'
        proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        res , err = proc.communicate()
        if err != "":
            raise Exception(err.split("\n"))

        res = res.split("\n")
        for line in res:
            if line.startswith("["):
                res = line

        if res == "":
            return []
        
        data = json.loads(res)
            
        return data
        
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

 ```
***

# Kuiper API

Kuiper has a limited feature API, check the repo [DFIRKuiperAPI](https://github.com/DFIRKuiper/DFIRKuiperAPI). 

- [GetFieldsScript](https://github.com/DFIRKuiper/DFIRKuiperAPI#GetFieldsScript): Retrieves parsed data from Kuiper.
- [UploadMachines](https://github.com/DFIRKuiper/DFIRKuiperAPI#UploadMachines): Upload new machine (.zip file) to specific case.


=======
To solve the issue run the command

```shell
sysctl -w vm.max_map_count=262144
```

2- Note: if you faced the following issue

```shell
Creating network "kuiper_kuiper" with driver "bridge"
Creating kuiper_es01    ... done
Creating kuiper_mongodb ... done
Creating kuiper_redis   ... done
Creating kuiper_flask   ... error
Creating kuiper_nfs     ... done
Creating kuiper_celery  ... 

ERROR: for kuiper_flask  Cannot start service flask: error while mounting volume '/var/lib/docker/volumes/kuiper_kuiper_nfs/_data': failed to mount local volume: mount :/:/var/lib/docker/vCreating kuiper_celery  ... done

ERROR: for flask  Cannot start service flask: error while mounting volume '/var/lib/docker/volumes/kuiper_kuiper_nfs/_data': failed to mount local volume: mount :/:/var/lib/docker/volumes/kuiper_kuiper_nfs/_data, data: addr=172.30.250.10: permission denied
ERROR: Encountered errors while bringing up the project.
```

To solve the issue, run the command again 

```shell
docker-compose up -d
```

# Kuiper API

Kuiper has a limited feature API, check the repo [DFIRKuiperAPI](https://github.com/DFIRKuiper/DFIRKuiperAPI). 

- [GetFieldsScript](https://github.com/DFIRKuiper/DFIRKuiperAPI#GetFieldsScript): Retrieves parsed data from Kuiper.
- [UploadMachines](https://github.com/DFIRKuiper/DFIRKuiperAPI#UploadMachines): Upload new machine (.zip file) to specific case.



# Issues Tracking and Contribution

We are happy to receive any issues, contribution, and ideas.

we appreciate sharing any parsers you develop, please send a pull request to be able to add it to the parsers list.


# Licenses

- Each parser has its own license, all parsers placed in the following folder  `/kuiper/parsers/`.

- All files in this project under GPL-3.0 license, unless mentioned otherwise.


# Creators

[Saleh Muhaysin](https://github.com/salehmuhaysin), Twitter ([@saleh_muhaysin](https://twitter.com/saleh_muhaysin)),

[Muteb Alqahtani](https://github.com/muteb), Twitter([@muteb_alqahtani](https://twitter.com/muteb_alqahtani))

[Abdullah Alrasheed](https://github.com/Abdullah-Alrasheed), Twitter([@abdullah_rush](https://twitter.com/abdullah_rush))
